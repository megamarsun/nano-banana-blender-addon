bl_info = {
    "name": "Nano-Banana (Gemini 2.5 Flash Image) Editor",
    "author": "あなた",
    "version": (0, 2, 0),
    "blender": (4, 0, 0),
    "location": "Image Editor > Nパネル > Nano-Banana",
    "description": "Gemini 2.5 Flash Image (通称 nano-banana) をAPI経由で叩いて画像編集/合成",
    "category": "Image",
}

import bpy, os, json, base64
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import AddonPreferences, Operator, Panel, PropertyGroup

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image-preview:generateContent"

# -------------------------
# Add-on Preferences
# -------------------------
class NBPreferences(AddonPreferences):
    bl_idname = __name__
    api_key: StringProperty(
        name="Gemini API Key",
        description="Google AI StudioのAPIキー",
        subtype='PASSWORD'
    )
    def draw(self, ctx):
        col = self.layout.column()
        col.prop(self, "api_key")


# -------------------------
# Scene Properties
# -------------------------
class NBProps(PropertyGroup):
    mode: EnumProperty(
        name="Mode",
        description="単一画像編集 or 2枚合成",
        items=[
            ('EDIT', "Edit (1 image)", "単一画像の局所編集/質感変換"),
            ('COMPOSE', "Compose (2 images)", "被写体+背景など2枚を合成")
        ],
        default='EDIT'
    )
    prompt: StringProperty(
        name="Edit Prompt",
        description="例: '髪に赤いリボンを追加。照明と色は維持。'",
        default=""
    )
    input_path: StringProperty(
        name="Input Image A",
        description="編集/被写体 画像ファイル(PNG/JPG)",
        default="",
        subtype='FILE_PATH'
    )
    input_path_b: StringProperty(
        name="Input Image B (optional)",
        description="背景/参照 画像ファイル(PNG/JPG) ※COMPOSE時のみ使用",
        default="",
        subtype='FILE_PATH'
    )
    output_path: StringProperty(
        name="Output Image",
        description="保存先PNGパス（未指定ならAと同じフォルダに nb_out.png）",
        default="",
        subtype='FILE_PATH'
    )
    open_in_image_editor: BoolProperty(
        name="Open Result in Image Editor",
        default=True
    )


# -------------------------
# Helpers
# -------------------------
def _abs(path):
    return bpy.path.abspath(path) if path else ""

def _file_to_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")

def _guess_mime(path):
    p = path.lower()
    if p.endswith(".png"):  return "image/png"
    if p.endswith(".jpg") or p.endswith(".jpeg"): return "image/jpeg"
    # デフォルトはPNG扱い
    return "image/png"

def _api_call(api_key: str, body: dict) -> dict:
    req = Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key.strip(),  # 400対策：キーはヘッダで
        }
    )
    with urlopen(req, timeout=180) as r:
        return json.loads(r.read().decode("utf-8"))

def _extract_image_b64(res: dict) -> str:
    """
    レスポンスから画像base64を取り出す。
    レスポンス表記は inline_data / inlineData の両系に対応。
    """
    try:
        parts = res["candidates"][0]["content"]["parts"]
    except Exception:
        return None
    for part in parts:
        if "inline_data" in part and "data" in part["inline_data"]:
            return part["inline_data"]["data"]
        if "inlineData" in part and "data" in part["inlineData"]:
            return part["inlineData"]["data"]
    return None


# -------------------------
# Operator
# -------------------------
class NB_OT_Run(Operator):
    bl_idname = "nb.run_edit"
    bl_label = "Run nano-banana"
    bl_description = "Gemini 2.5 Flash Imageで画像編集/合成を実行"

    def execute(self, ctx):
        prefs = ctx.preferences.addons[__name__].preferences
        props = ctx.scene.nb_props

        api_key = (prefs.api_key or "").strip()
        if not api_key:
            self.report({'ERROR'}, "APIキー未設定（Edit > Preferences > Add-ons で設定）")
            return {'CANCELLED'}

        in_a = _abs(props.input_path)
        if not in_a or not os.path.isfile(in_a):
            self.report({'ERROR'}, "Input Image A が見つかりません")
            return {'CANCELLED'}

        # 画像読み込み（2枚目は任意）
        mime_a = _guess_mime(in_a)
        b64_a  = _file_to_b64(in_a)

        parts = [
            {"text": props.prompt or "Edit subtly. Keep identity, lighting, and colors."},
            {"inline_data": {"mime_type": mime_a, "data": b64_a}},
        ]

        if props.mode == 'COMPOSE':
            in_b = _abs(props.input_path_b)
            if not in_b or not os.path.isfile(in_b):
                self.report({'ERROR'}, "Composeモード: Input Image B が見つかりません")
                return {'CANCELLED'}
            mime_b = _guess_mime(in_b)
            b64_b  = _file_to_b64(in_b)
            # 2枚目も同じターンに積む（被写体→背景の順推奨だが固定ではない）
            parts.append({"inline_data": {"mime_type": mime_b, "data": b64_b}})

        body = {"contents": [{"parts": parts}]}

        # API呼び出し
        try:
            res = _api_call(api_key, body)
        except HTTPError as e:
            self.report({'ERROR'}, f"HTTP失敗: {e}（URL/ヘッダ/請求設定を確認）")
            return {'CANCELLED'}
        except URLError as e:
            self.report({'ERROR'}, f"接続失敗: {e}")
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"不明な通信エラー: {e}")
            return {'CANCELLED'}

        # サーバー側エラー
        if isinstance(res, dict) and "error" in res:
            msg = res["error"].get("message", "Unknown error")
            self.report({'ERROR'}, f"APIエラー: {msg}")
            return {'CANCELLED'}

        # 画像抽出
        img_b64 = _extract_image_b64(res)
        if not img_b64:
            # テキスト応答デバッグ
            try:
                parts_res = res["candidates"][0]["content"]["parts"]
                txt = "".join([p.get("text","") for p in parts_res if "text" in p])
            except Exception:
                txt = ""
            self.report({'ERROR'}, f"画像が返りませんでした。プロンプトを簡潔化/保持要素を明記して再試行。{(' メッセージ: ' + txt[:200]) if txt else ''}")
            return {'CANCELLED'}

        # 保存パス決定
        out_path = _abs(props.output_path)
        if not out_path:
            base_dir = os.path.dirname(in_a) if os.path.dirname(in_a) else bpy.path.abspath("//")
            out_path = os.path.join(base_dir, "nb_out.png")

        # 書き出し
        try:
            with open(out_path, "wb") as f:
                f.write(base64.b64decode(img_b64))
        except Exception as e:
            self.report({'ERROR'}, f"保存に失敗: {e}")
            return {'CANCELLED'}

        # Image Editor に読み込み
        if props.open_in_image_editor:
            try:
                img = bpy.data.images.load(out_path, check_existing=True)
                for area in ctx.screen.areas:
                    if area.type == 'IMAGE_EDITOR':
                        area.spaces.active.image = img
                        break
            except Exception:
                # 読み込みに失敗しても致命ではない
                pass

        self.report({'INFO'}, f"保存: {out_path}")
        return {'FINISHED'}


# -------------------------
# UI Panel
# -------------------------
class NB_PT_Panel(Panel):
    bl_label = "Nano-Banana (Gemini Image)"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Nano-Banana"

    def draw(self, ctx):
        p = ctx.scene.nb_props
        layout = self.layout

        box = layout.box()
        box.label(text="Mode")
        box.prop(p, "mode", expand=True)

        col = layout.column(align=True)
        col.prop(p, "input_path")

        if p.mode == 'COMPOSE':
            col.prop(p, "input_path_b")

        layout.prop(p, "prompt")
        layout.prop(p, "output_path")
        layout.prop(p, "open_in_image_editor")
        layout.operator("nb.run_edit", icon='PLAY')


# -------------------------
# Register
# -------------------------
classes = (
    NBPreferences,
    NBProps,
    NB_OT_Run,
    NB_PT_Panel,
)

def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.nb_props = bpy.props.PointerProperty(type=NBProps)

def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
    del bpy.types.Scene.nb_props

if __name__ == "__main__":
    register()
