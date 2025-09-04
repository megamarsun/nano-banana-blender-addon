bl_info = {
    "name": "Nano-Banana (Gemini 2.5 Flash Image) Editor",
    "author": "あなた",
    "version": (0, 3, 0),
    "blender": (4, 0, 0),
    "location": "Image Editor > Nパネル > Nano-Banana",
    "description": "Gemini 2.5 Flash Image (通称 nano-banana) をAPI経由で叩いて画像編集/合成（参照2+レンダ1。レンダ完了で自動実行）",
    "category": "Image",
}

import bpy, os, json, base64
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty
from bpy.types import AddonPreferences, Operator, Panel, PropertyGroup

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image-preview:generateContent"

# ==== 追加: モジュール内グローバル（ハンドラ重複登録防止） ====
_NB_HANDLER_TAG = "_nb_auto_render_handler_registered"

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
    # 既存
    mode: EnumProperty(
        name="Mode",
        description="単一画像編集 or 参照合成",
        items=[
            ('EDIT', "Edit (1 image)", "単一画像の局所編集/質感変換"),
            ('COMPOSE', "Compose (Refs+Render)", "参照×2 + レンダ（最後が加工対象）")
        ],
        default='EDIT'
    )
    prompt: StringProperty(
        name="Edit Prompt",
        description="例: '色・構図は維持。フィギュアの質感に。'",
        default=""
    )
    # 入力（表示名を実態に合わせて変更）
    input_path: StringProperty(
        name="Render (Base) Image",
        description="最後に渡す加工対象（レンダ）PNG/JPG（必須）",
        default="",
        subtype='FILE_PATH'
    )
    input_path_b: StringProperty(
        name="Ref 1 (optional)",
        description="色/背景/質感など参照画像（任意）",
        default="",
        subtype='FILE_PATH'
    )
    # 追加: 参照2枚目
    input_path_c: StringProperty(
        name="Ref 2 (optional)",
        description="追加の参照画像（任意）",
        default="",
        subtype='FILE_PATH'
    )
    output_path: StringProperty(
        name="Output Image (manual)",
        description="手動実行の保存先。未指定ならレンダ画像と同フォルダに nb_out.png",
        default="",
        subtype='FILE_PATH'
    )
    open_in_image_editor: BoolProperty(
        name="Open Result in Image Editor (manual)",
        default=True
    )

    # ==== 追加: レンダ連動 ====
    auto_on_render: BoolProperty(
        name="Auto Run on Render",
        description="レンダ完了のたびにAI生成を実行（連番保存）",
        default=False
    )
    auto_out_dir: StringProperty(
        name="Auto Output Dir",
        description="レンダ連動の保存先フォルダ（例: //nb_out）",
        default="//nb_out",
        subtype='DIR_PATH'
    )

    # ==== 追加: リミッター ====
    limit_enabled: BoolProperty(
        name="Use Limiter",
        description="API実行回数の上限を設定。上限到達で自動停止",
        default=True
    )
    limit_max: IntProperty(
        name="Max Calls",
        description="上限回数（例: 100）",
        default=100, min=1, soft_max=10000
    )
    limit_count: IntProperty(
        name="Used",
        description="現在の実行回数（自動カウント）",
        default=0, min=0
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
    return "image/png"

def _api_call(api_key: str, body: dict) -> dict:
    req = Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key.strip(),
        }
    )
    with urlopen(req, timeout=180) as r:
        return json.loads(r.read().decode("utf-8"))

def _extract_image_b64(res: dict) -> str:
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

# ==== 追加: プロンプト補強（ゼロ生成抑止 & Base保持） ====
def _augment_prompt(user_text: str) -> str:
    guard = (
        "ゼロからの新規生成は禁止。最後の画像（レンダ）を加工対象とし、"
        "構図・カメラ・照明・解像度・アスペクト比・被写体の形状を保持。"
        "参照画像は色味/質感/雰囲気の手掛かりのみとして用いる。"
    )
    base = (user_text or "").strip()
    return (base + ("\n" if base else "") + guard)

# ==== 追加: 共通実行（Refs→Refs→最後にRender） ====
def _run_nano_banana(api_key: str, prompt: str, ref1: str, ref2: str, render_img: str) -> bytes:
    parts = [{"text": _augment_prompt(prompt)}]

    # 参照は先に（任意）
    if ref1 and os.path.isfile(ref1):
        parts.append({"inline_data": {"mime_type": _guess_mime(ref1), "data": _file_to_b64(ref1)}})
    if ref2 and os.path.isfile(ref2):
        parts.append({"inline_data": {"mime_type": _guess_mime(ref2), "data": _file_to_b64(ref2)}})

    # 最後にレンダ（必須）
    if not render_img or not os.path.isfile(render_img):
        raise FileNotFoundError("Render (Base) Image が見つかりません")
    parts.append({"inline_data": {"mime_type": _guess_mime(render_img), "data": _file_to_b64(render_img)}})

    body = {"contents": [{"parts": parts}]}
    res = _api_call(api_key, body)

    if isinstance(res, dict) and "error" in res:
        code = res["error"].get("code")
        status = res["error"].get("status")
        msg = res["error"].get("message", "Unknown error")
        raise RuntimeError(f"APIエラー: {code}/{status} {msg}")

    img_b64 = _extract_image_b64(res)
    if not img_b64:
        raise RuntimeError("画像が返りませんでした（プロンプトを簡潔化/保持要素を明記）")

    return base64.b64decode(img_b64)

def _ensure_dir(path_dir: str):
    if path_dir:
        os.makedirs(path_dir, exist_ok=True)

# ==== 追加: レンダ完了ハンドラ（各フレームごと） ====
def _nb_on_render_write(scene):
    try:
        props = scene.nb_props
    except Exception:
        return

    if not getattr(props, "auto_on_render", False):
        return

    # リミッター判定
    if props.limit_enabled and props.limit_count >= props.limit_max:
        props.auto_on_render = False
        bpy.ops.nb.toggle_auto_on_render('INVOKE_DEFAULT', enable=False)  # UI連動
        print("[Nano-Banana] Limiter reached. Auto disabled.")
        return

    # 入力（Refs & Render）
    prefs = bpy.context.preferences.addons[__name__].preferences
    api_key = (prefs.api_key or "").strip()
    if not api_key:
        print("[Nano-Banana] APIキー未設定。スキップ")
        return

    # レンダ結果を一時保存（フレームごと）— Render Result から保存する
    frame = scene.frame_current
    base_dir = bpy.path.abspath(props.auto_out_dir) if props.auto_out_dir else bpy.path.abspath("//nb_out")
    in_dir = os.path.join(base_dir, "in")
    out_dir = os.path.join(base_dir, "out")
    _ensure_dir(in_dir); _ensure_dir(out_dir)

    # 入力レンダの保存先（PNG固定）
    render_png = os.path.join(in_dir, f"render_{frame:04d}.png")
    try:
        # Render Result を保存
        img = bpy.data.images.get("Render Result")
        if img is None:
            print("[Nano-Banana] Render Result が見つかりません。スキップ")
            return
        img.save_render(render_png, scene=scene)
    except Exception as e:
        print(f"[Nano-Banana] レンダ保存失敗: {e}")
        return

    # 参照（任意）
    ref1 = _abs(props.input_path_b) if props.input_path_b else ""
    ref2 = _abs(props.input_path_c) if props.input_path_c else ""

    # 推論実行
    try:
        data = _run_nano_banana(api_key, props.prompt, ref1, ref2, render_png)
    except Exception as e:
        print(f"[Nano-Banana] 推論失敗: {e}")
        return

    # 出力保存（連番）
    out_png = os.path.join(out_dir, f"nb_out_{frame:04d}.png")
    try:
        with open(out_png, "wb") as f:
            f.write(data)
    except Exception as e:
        print(f"[Nano-Banana] 出力保存失敗: {e}")
        return

    # カウント加算
    props.limit_count += 1
    print(f"[Nano-Banana] Frame {frame} → {out_png}  (count {props.limit_count}/{props.limit_max})")


# -------------------------
# Operator（手動実行は従来どおり）
# -------------------------
class NB_OT_Run(Operator):
    bl_idname = "nb.run_edit"
    bl_label = "Run nano-banana (manual)"
    bl_description = "Gemini 2.5 Flash Imageで手動実行（参照→参照→レンダの順）"

    def execute(self, ctx):
        prefs = ctx.preferences.addons[__name__].preferences
        props = ctx.scene.nb_props

        api_key = (prefs.api_key or "").strip()
        if not api_key:
            self.report({'ERROR'}, "APIキー未設定（Edit > Preferences > Add-ons で設定）")
            return {'CANCELLED'}

        # 入力ファイル
        in_a = _abs(props.input_path)  # Render(Base)
        ref1 = _abs(props.input_path_b) if props.input_path_b else ""
        ref2 = _abs(props.input_path_c) if props.input_path_c else ""

        try:
            data = _run_nano_banana(api_key, props.prompt, ref1, ref2, in_a)
        except FileNotFoundError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"{e}")
            return {'CANCELLED'}

        # 保存パス（手動）
        out_path = _abs(props.output_path).strip()
        if not out_path:
            base_dir = os.path.dirname(in_a) if os.path.dirname(in_a) else bpy.path.abspath("//")
            out_path = os.path.join(base_dir, "nb_out.png")
        else:
            # フォルダ指定にも対応
            is_dir_like = out_path.endswith(("/", "\\")) or os.path.isdir(out_path) or (os.path.splitext(out_path)[1] == "")
            if is_dir_like:
                out_dir = out_path.rstrip("/\\")
                _ensure_dir(out_dir)
                out_path = os.path.join(out_dir, "nb_out.png")
            else:
                out_dir = os.path.dirname(out_path) or bpy.path.abspath("//")
                _ensure_dir(out_dir)

        try:
            with open(out_path, "wb") as f:
                f.write(data)
        except Exception as e:
            self.report({'ERROR'}, f"保存に失敗: {e}")
            return {'CANCELLED'}

        if props.open_in_image_editor:
            try:
                img = bpy.data.images.load(out_path, check_existing=True)
                for area in ctx.screen.areas:
                    if area.type == 'IMAGE_EDITOR':
                        area.spaces.active.image = img
                        break
            except Exception:
                pass

        self.report({'INFO'}, f"保存: {out_path}")
        return {'FINISHED'}


# ==== 追加: 自動ON/OFF用オペレータ ====
class NB_OT_ToggleAuto(Operator):
    bl_idname = "nb.toggle_auto_on_render"
    bl_label = "Toggle Auto Run on Render"
    bl_description = "レンダ完了のたびにAI生成を自動実行するON/OFF"

    enable: BoolProperty(default=True)

    def execute(self, ctx):
        scene = ctx.scene
        props = scene.nb_props
        props.auto_on_render = self.enable

        # ハンドラ登録/解除
        if self.enable:
            if not getattr(bpy.app.handlers, _NB_HANDLER_TAG, False):
                if _nb_on_render_write not in bpy.app.handlers.render_write:
                    bpy.app.handlers.render_write.append(_nb_on_render_write)
                setattr(bpy.app.handlers, _NB_HANDLER_TAG, True)
            self.report({'INFO'}, "Auto Run: 有効")
        else:
            if _nb_on_render_write in bpy.app.handlers.render_write:
                bpy.app.handlers.render_write.remove(_nb_on_render_write)
            setattr(bpy.app.handlers, _NB_HANDLER_TAG, False)
            self.report({'INFO'}, "Auto Run: 無効")

        return {'FINISHED'}


# ==== 追加: カウンターを手動でリセット ====
class NB_OT_ResetCounter(Operator):
    bl_idname = "nb.reset_counter"
    bl_label = "Reset Limiter Counter"
    bl_description = "使用回数カウンタを0に戻す"

    def execute(self, ctx):
        ctx.scene.nb_props.limit_count = 0
        self.report({'INFO'}, "カウンタを0にしました")
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

        # Refs → Render（順序をUIでも示す）
        col = layout.column(align=True)
        if p.mode == 'COMPOSE':
            col.label(text="References (up to 2)")
            col.prop(p, "input_path_b")
            col.prop(p, "input_path_c")

        layout.separator()
        layout.label(text="Render (Base) - required")
        layout.prop(p, "input_path")

        layout.separator()
        layout.prop(p, "prompt")

        layout.separator()
        col = layout.column(align=True)
        col.label(text="Manual Run")
        col.prop(p, "output_path")
        col.prop(p, "open_in_image_editor")
        col.operator("nb.run_edit", icon='PLAY')

        layout.separator()
        col = layout.box().column(align=True)
        col.label(text="Auto Run on Render (per-frame)")
        row = col.row(align=True)
        row.prop(p, "auto_on_render", text="Enabled")
        on = col.operator("nb.toggle_auto_on_render", text="Apply", icon='CHECKMARK')
        on.enable = p.auto_on_render
        col.prop(p, "auto_out_dir")

        layout.separator()
        col = layout.box().column(align=True)
        col.label(text="Limiter")
        col.prop(p, "limit_enabled")
        row = col.row(align=True)
        row.prop(p, "limit_max")
        row.prop(p, "limit_count")
        col.operator("nb.reset_counter", icon='RECOVER_LAST')


# -------------------------
# Register
# -------------------------
classes = (
    NBPreferences,
    NBProps,
    NB_OT_Run,
    NB_OT_ToggleAuto,
    NB_OT_ResetCounter,
    NB_PT_Panel,
)

def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.nb_props = bpy.props.PointerProperty(type=NBProps)

def unregister():
    # ハンドラ解除（万一の重複回避）
    if _nb_on_render_write in bpy.app.handlers.render_write:
        bpy.app.handlers.render_write.remove(_nb_on_render_write)
    if hasattr(bpy.app.handlers, _NB_HANDLER_TAG):
        delattr(bpy.app.handlers, _NB_HANDLER_TAG)

    for c in reversed(classes):
        bpy.utils.unregister_class(c)
    del bpy.types.Scene.nb_props

if __name__ == "__main__":
    register()
