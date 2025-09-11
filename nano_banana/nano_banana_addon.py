import bpy, os, json, base64, datetime, threading, queue, tempfile, time, uuid, re
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty
from bpy.types import AddonPreferences, Operator, Panel, PropertyGroup
from bpy.app.translations import pgettext_iface as _

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image-preview:generateContent"

# =========================================================
# 内部状態
# =========================================================
_NB_HANDLER_REGISTERED = False  # render_write ハンドラ重複登録防止

# =========================================================
# Add-on Preferences
# =========================================================
ADDON_NAME = __package__ if __package__ else __name__


class NBPreferences(AddonPreferences):
    bl_idname = ADDON_NAME
    api_key: StringProperty(
        name="Gemini API Key",
        description="Google AI StudioのAPIキー",
        subtype='PASSWORD'
    )
    def draw(self, ctx):
        col = self.layout.column()
        col.prop(self, "api_key")

# =========================================================
# Scene Properties
# =========================================================
class NBProps(PropertyGroup):
    # モード（手動UIの見た目用）
    mode: EnumProperty(
        name="Mode",
        description="単一編集 or 参照合成",
        items=[
            ('EDIT', "Edit (1 image)", "単一画像の局所編集/質感変換"),
            ('COMPOSE', "Compose (Refs+Render)", "参照×2 + レンダ（最後が加工対象）")
        ],
        default='COMPOSE'
    )

    # 入力
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
    input_path_c: StringProperty(
        name="Ref 2 (optional)",
        description="追加の参照画像（任意）",
        default="",
        subtype='FILE_PATH'
    )

    # 手動実行
    prompt: StringProperty(
        name="Edit Prompt",
        description="例: '色・構図は維持。フィギュアの質感に。'",
        default=""
    )
    output_path: StringProperty(
        name="Output Image (manual)",
        description="手動実行の保存先。未指定ならレンダ画像と同フォルダに nb_out.png",
        default="",
        subtype='FILE_PATH'
    )

    # 自動実行（レンダ連動）
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

    # リミッター
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

    # ログ設定・状態
    verbose: BoolProperty(
        name="Verbose (Console + Text + File)",
        description="システムコンソール/テキストブロック/nb_log.txtに出力",
        default=True
    )
    last_info: StringProperty(
        name="Last Info",
        description="直近の情報ログ（読み取り専用）",
        default=""
    )
    last_error: StringProperty(
        name="Last Error",
        description="直近のエラーログ（読み取り専用）",
        default=""
    )
    log_dir: StringProperty(
        name="Log Dir",
        description="ログファイル(nb_log.txt)の保存先（未指定なら //nb_out ）",
        default="",
        subtype='DIR_PATH'
    )

    # 生成画像の保存先や適用先の設定
    save_location: EnumProperty(
        name="Save Location",
        items=[
            ('TEMP', "Temp", "システムの一時ディレクトリに保存"),
            ('PROJECT', "Project Relative Textures", "//textures に保存"),
            ('ABSOLUTE', "Absolute Path", "Output Imageで指定した絶対パス"),
        ],
        default='TEMP',
    )
    apply_to: EnumProperty(
        name="Apply To",
        items=[
            ('NONE', "None", "特に適用しない"),
            ('IMAGE_EDITOR', "Image Editor", "Image Editor に表示"),
            ('ACTIVE_OBJECT_MATERIAL', "Active Object Material", "アクティブオブジェクトのマテリアルに割り当て"),
            ('COMPOSITOR', "Compositor", "コンポジターに画像ノードを追加"),
        ],
        default='IMAGE_EDITOR',
    )
    pack_image: BoolProperty(
        name="Pack Image",
        default=False,
    )
    show_toast: BoolProperty(
        name="Show Toast",
        default=True,
    )
    overwrite_existing: BoolProperty(
        name="Overwrite Existing",
        default=False,
    )

# =========================================================
# Helpers（ログ）
# =========================================================
def _now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _log_write_to_textblock(line: str):
    name = "NanoBananaLog"
    txt = bpy.data.texts.get(name) or bpy.data.texts.new(name)
    txt.write(line + "\n")

def _log_write_to_file(path_dir: str, line: str):
    try:
        if not path_dir:
            path_dir = bpy.path.abspath("//nb_out")
        os.makedirs(path_dir, exist_ok=True)
        with open(os.path.join(path_dir, "nb_log.txt"), "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def nb_log(scene, level: str, msg: str):
    """Console + Scene Props + Text + File に出力"""
    ts = _now()
    line = f"[{ts}] [{level}] {msg}"
    print("[Nano-Banana]", line)  # Console

    try:
        p = scene.nb_props
        if level == "ERROR":
            p.last_error = line
        else:
            p.last_info = line
        if p.verbose:
            _log_write_to_textblock(line)
            _log_write_to_file(bpy.path.abspath(p.log_dir) if p.log_dir else None, line)
    except Exception:
        pass

# =========================================================
# Helpers（API/入出力）
# =========================================================
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

def _ensure_dir(path_dir: str):
    if path_dir:
        os.makedirs(path_dir, exist_ok=True)

def _api_call(api_key: str, body: dict, cancel_event=None, timeout: int = 10, max_attempts: int = 5) -> dict:
    """APIを呼び出し、指数バックオフ付きでリトライする"""
    wait = 1
    for attempt in range(max_attempts):
        if cancel_event and cancel_event.is_set():
            raise RuntimeError("Cancelled")
        req = Request(
            API_URL,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key.strip(),
            }
        )
        try:
            with urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except (URLError, HTTPError) as e:
            if attempt == max_attempts - 1:
                raise
            time.sleep(wait)
            wait = min(wait * 2, 8)

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

def _augment_prompt(user_text: str) -> str:
    guard = (
        "ゼロからの新規生成は禁止。最後の画像（レンダ）を加工対象とし、"
        "構図・カメラ・照明・解像度・アスペクト比・被写体の形状を保持。"
        "参照画像は色味/質感/雰囲気の手掛かりのみとして用いる。"
    )
    base = (user_text or "").strip()
    return (base + ("\n" if base else "") + guard)

def _run_nano_banana(api_key: str, prompt: str, ref1: str, ref2: str, render_img: str, cancel_event=None) -> bytes:
    parts = [{"text": _augment_prompt(prompt)}]

    if ref1 and os.path.isfile(ref1):
        parts.append({"inline_data": {"mime_type": _guess_mime(ref1), "data": _file_to_b64(ref1)}})
    if ref2 and os.path.isfile(ref2):
        parts.append({"inline_data": {"mime_type": _guess_mime(ref2), "data": _file_to_b64(ref2)}})

    if not render_img or not os.path.isfile(render_img):
        raise FileNotFoundError("Render (Base) Image が見つかりません")
    parts.append({"inline_data": {"mime_type": _guess_mime(render_img), "data": _file_to_b64(render_img)}})

    body = {"contents": [{"parts": parts}]}
    res = _api_call(api_key, body, cancel_event=cancel_event)

    if isinstance(res, dict) and "error" in res:
        code = res["error"].get("code")
        status = res["error"].get("status")
        msg = res["error"].get("message", "Unknown error")
        raise RuntimeError(f"APIエラー: {code}/{status} {msg}")

    img_b64 = _extract_image_b64(res)
    if not img_b64:
        raise RuntimeError("画像が返りませんでした（プロンプトを簡潔化/保持要素を明記）")
    return base64.b64decode(img_b64)


# =========================================================
# Helpers（保存/適用）
# =========================================================
def _sanitize_filename(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", name)


def _unique_path(base_dir: str, name: str, overwrite: bool) -> str:
    os.makedirs(base_dir, exist_ok=True)
    name = _sanitize_filename(name)
    path = os.path.join(base_dir, name)
    if overwrite or not os.path.exists(path):
        return path
    stem, ext = os.path.splitext(name)
    return os.path.join(base_dir, f"{stem}_{uuid.uuid4().hex}{ext}")


def _save_image_bytes(data: bytes, props) -> str:
    if props.save_location == 'PROJECT':
        base_dir = bpy.path.abspath("//textures")
    elif props.save_location == 'ABSOLUTE' and props.output_path:
        base_dir = os.path.dirname(_abs(props.output_path)) or tempfile.gettempdir()
    else:
        base_dir = tempfile.gettempdir()
    filename = os.path.basename(props.output_path) if props.output_path else "nb_out.png"
    path = _unique_path(base_dir, filename, props.overwrite_existing)
    with open(path, "wb") as f:
        f.write(data)
    return path


def _apply_image(path: str, props, ctx):
    img = bpy.data.images.load(path, check_existing=True)
    if props.pack_image:
        img.pack()

    if props.apply_to == 'IMAGE_EDITOR':
        for area in ctx.screen.areas:
            if area.type == 'IMAGE_EDITOR':
                area.spaces.active.image = img
                break
    elif props.apply_to == 'ACTIVE_OBJECT_MATERIAL':
        obj = ctx.object
        if obj and obj.type == 'MESH':
            mat = obj.active_material
            if mat is None:
                mat = bpy.data.materials.new(name="NanoBananaMat")
                obj.data.materials.append(mat)
            mat.use_nodes = True
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links
            tex = nodes.new("ShaderNodeTexImage")
            tex.image = img
            bsdf = nodes.get("Principled BSDF")
            if bsdf:
                links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    elif props.apply_to == 'COMPOSITOR':
        scene = ctx.scene
        if scene.use_nodes:
            nt = scene.node_tree
            img_node = nt.nodes.new("CompositorNodeImage")
            img_node.image = img
    return img


def _async_run(api_key, prompt, ref1, ref2, render_img, q, cancel_event):
    """バックグラウンドで推論を実行し、キューで進捗や結果を送る"""
    try:
        q.put(("progress", 10))
        data = _run_nano_banana(api_key, prompt, ref1, ref2, render_img, cancel_event=cancel_event)
        if cancel_event.is_set():
            q.put(("canceled", None))
            return
        q.put(("progress", 100))
        q.put(("result", data))
    except Exception as e:
        q.put(("error", str(e)))

# =========================================================
# Render ハンドラ
# =========================================================
def _nb_on_render_write(scene):
    """レンダ結果をPNG保存→API実行→連番で保存。ログは nb_log へ。"""
    try:
        props = scene.nb_props
    except Exception:
        return

    if not getattr(props, "auto_on_render", False):
        return

    # リミッター判定
    if props.limit_enabled and props.limit_count >= props.limit_max:
        props.auto_on_render = False
        nb_log(scene, "INFO", "Limiter reached. Auto disabled.")
        return

    # APIキー確認
    prefs = bpy.context.preferences.addons[ADDON_NAME].preferences
    api_key = (prefs.api_key or "").strip()
    if not api_key:
        nb_log(scene, "ERROR", "APIキー未設定。Auto処理をスキップ")
        return

    # 保存先準備
    frame = scene.frame_current
    base_dir = bpy.path.abspath(props.auto_out_dir) if props.auto_out_dir else bpy.path.abspath("//nb_out")
    in_dir = os.path.join(base_dir, "in")
    out_dir = os.path.join(base_dir, "out")
    _ensure_dir(in_dir); _ensure_dir(out_dir)

    # Render Result 取得・保存
    render_png = os.path.join(in_dir, f"render_{frame:04d}.png")
    try:
        img = bpy.data.images.get("Render Result")
        if img is None:
            nb_log(scene, "ERROR", "Render Result が見つかりません。スキップ")
            return
        img.save_render(render_png, scene=scene)
    except Exception as e:
        nb_log(scene, "ERROR", f"レンダ保存失敗: {e}")
        return

    # 参照（任意）
    ref1 = _abs(props.input_path_b) if props.input_path_b else ""
    ref2 = _abs(props.input_path_c) if props.input_path_c else ""

    # 推論
    try:
        data = _run_nano_banana(api_key, props.prompt, ref1, ref2, render_png)
    except Exception as e:
        nb_log(scene, "ERROR", f"推論失敗: {e}")
        return

    # 出力保存（連番）
    out_png = os.path.join(out_dir, f"nb_out_{frame:04d}.png")
    try:
        with open(out_png, "wb") as f:
            f.write(data)
    except Exception as e:
        nb_log(scene, "ERROR", f"出力保存失敗: {e}")
        return

    # カウント加算
    props.limit_count += 1
    nb_log(scene, "INFO", f"Frame {frame} → {out_png}  (count {props.limit_count}/{props.limit_max})")

# =========================================================
# Operators
# =========================================================
class NB_OT_Run(Operator):
    bl_idname = "nb.run_edit"
    bl_label = "Run nano-banana (manual)"
    bl_description = "参照→参照→レンダの順でAPI実行して保存"

    def _finish(self, ctx):
        wm = ctx.window_manager
        try:
            wm.progress_end()
        except Exception:
            pass
        if hasattr(self, "_timer") and self._timer:
            wm.event_timer_remove(self._timer)
            self._timer = None

    def invoke(self, ctx, event):
        scene = ctx.scene
        prefs = ctx.preferences.addons[ADDON_NAME].preferences
        props = scene.nb_props

        api_key = (prefs.api_key or "").strip()
        if not api_key:
            self.report({'ERROR'}, "APIキー未設定（Edit > Preferences > Add-ons で設定）")
            nb_log(scene, "ERROR", "APIキー未設定（手動）")
            return {'CANCELLED'}

        in_a = _abs(props.input_path)
        if not os.path.isfile(in_a):
            self.report({'ERROR'}, "Render (Base) Image が見つかりません")
            nb_log(scene, "ERROR", "Render (Base) Image が見つかりません")
            return {'CANCELLED'}
        ref1 = _abs(props.input_path_b) if props.input_path_b else ""
        ref2 = _abs(props.input_path_c) if props.input_path_c else ""

        self.scene = scene
        self.props = props
        self._queue = queue.Queue()
        self._cancel = threading.Event()
        self._thread = threading.Thread(
            target=_async_run,
            args=(api_key, props.prompt, ref1, ref2, in_a, self._queue, self._cancel),
            daemon=True,
        )
        self._thread.start()

        wm = ctx.window_manager
        wm.progress_begin(0, 100)
        self._timer = wm.event_timer_add(0.2, window=ctx.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, ctx, event):
        if event.type == 'ESC':
            self._cancel.set()
            return {'RUNNING_MODAL'}

        wm = ctx.window_manager
        while True:
            try:
                kind, payload = self._queue.get_nowait()
            except queue.Empty:
                break

            if kind == 'progress':
                wm.progress_update(payload)
            elif kind == 'result':
                path = _save_image_bytes(payload, self.props)
                _apply_image(path, self.props, ctx)
                if self.props.show_toast:
                    self.report({'INFO'}, f"保存: {path}")
                nb_log(self.scene, 'INFO', f"保存: {path}")
                self._finish(ctx)
                return {'FINISHED'}
            elif kind == 'error':
                if self.props.show_toast:
                    self.report({'ERROR'}, payload)
                nb_log(self.scene, 'ERROR', payload)
                self._finish(ctx)
                return {'CANCELLED'}
            elif kind == 'canceled':
                if self.props.show_toast:
                    self.report({'INFO'}, "キャンセルしました")
                nb_log(self.scene, 'INFO', "キャンセルされました")
                self._finish(ctx)
                return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def cancel(self, ctx):
        self._cancel.set()
        self._finish(ctx)

class NB_OT_ToggleAuto(Operator):
    bl_idname = "nb.toggle_auto_on_render"
    bl_label = "Apply Auto Run on Render"
    bl_description = "レンダ完了のたびにAI生成を自動実行するON/OFFを適用"
    enable: BoolProperty(default=True)

    def execute(self, ctx):
        global _NB_HANDLER_REGISTERED
        scene = ctx.scene
        props = scene.nb_props
        props.auto_on_render = self.enable

        if self.enable:
            if not _NB_HANDLER_REGISTERED:
                if _nb_on_render_write not in bpy.app.handlers.render_write:
                    bpy.app.handlers.render_write.append(_nb_on_render_write)
                _NB_HANDLER_REGISTERED = True
            nb_log(scene, "INFO", "Auto Run: 有効（render_write に登録）")
        else:
            if _nb_on_render_write in bpy.app.handlers.render_write:
                bpy.app.handlers.render_write.remove(_nb_on_render_write)
            _NB_HANDLER_REGISTERED = False
            nb_log(scene, "INFO", "Auto Run: 無効（render_write から解除）")
        return {'FINISHED'}

class NB_OT_ResetCounter(Operator):
    bl_idname = "nb.reset_counter"
    bl_label = "Reset Limiter Counter"
    bl_description = "使用回数カウンタを0に戻す"

    def execute(self, ctx):
        ctx.scene.nb_props.limit_count = 0
        nb_log(ctx.scene, "INFO", "カウンタを0にしました")
        return {'FINISHED'}

class NB_OT_ShowLastLog(Operator):
    bl_idname = "nb.show_last_log"
    bl_label = "Show Last Log"

    kind: EnumProperty(
        items=[('INFO', 'Info', ''), ('ERROR', 'Error', '')],
        default='INFO'
    )

    def execute(self, ctx):
        p = ctx.scene.nb_props
        text = p.last_info if self.kind == 'INFO' else p.last_error
        msg = text or "(no logs)"

        def draw(self2, context):
            self2.layout.label(text=self.kind)
            col = self2.layout.column()
            for line in msg.splitlines():
                col.label(text=line)

        bpy.context.window_manager.popup_menu(
            draw, title="Nano-Banana Log",
            icon='INFO' if self.kind=='INFO' else 'ERROR'
        )
        return {'FINISHED'}

# =========================================================
# UI Panel
# =========================================================
class NB_PT_Panel(Panel):
    bl_label = "Nano-Banana (Gemini Image)"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Nano-Banana"

    def draw(self, ctx):
        p = ctx.scene.nb_props
        layout = self.layout

        box = layout.box()
        box.label(text=_("Mode"))
        box.prop(p, "mode", expand=True)

        col = layout.column(align=True)
        if p.mode == 'COMPOSE':
            col.label(text=_("References (up to 2)"))
            col.prop(p, "input_path_b")
            col.prop(p, "input_path_c")

        layout.separator()
        layout.label(text=_("Render (Base) - required"))
        layout.prop(p, "input_path")

        layout.separator()
        layout.prop(p, "prompt")

        layout.separator()
        col = layout.column(align=True)
        col.label(text=_("Manual Run"))
        col.prop(p, "output_path")
        col.prop(p, "save_location")
        col.prop(p, "apply_to")
        col.prop(p, "pack_image")
        col.prop(p, "show_toast")
        col.prop(p, "overwrite_existing")
        col.operator("nb.run_edit", icon='PLAY')

        layout.separator()
        col = layout.box().column(align=True)
        col.label(text=_("Auto Run on Render (per-frame)"))
        row = col.row(align=True)
        row.prop(p, "auto_on_render", text=_("Enabled"))
        on = col.operator("nb.toggle_auto_on_render", text=_("Apply"), icon='CHECKMARK')
        on.enable = p.auto_on_render
        col.prop(p, "auto_out_dir")

        layout.separator()
        col = layout.box().column(align=True)
        col.label(text=_("Limiter"))
        col.prop(p, "limit_enabled")
        row = col.row(align=True)
        row.prop(p, "limit_max")
        row.prop(p, "limit_count")
        col.operator("nb.reset_counter", icon='RECOVER_LAST')

        layout.separator()
        box = layout.box()
        box.label(text=_("Logs"))
        row = box.row()
        row.prop(p, "verbose", text=_("Verbose"))
        row = box.row(align=True)
        row.prop(p, "log_dir", text=_("Log Dir"))
        if p.last_info:
            box.label(text=_("Last Info: ") + p.last_info[-80:], icon='INFO')
        if p.last_error:
            box.label(text=_("Last Error: ") + p.last_error[-80:], icon='ERROR')
        row = box.row(align=True)
        op = row.operator("nb.show_last_log", text=_("Show Last Info"), icon='INFO')
        op.kind = 'INFO'
        op = row.operator("nb.show_last_log", text=_("Show Last Error"), icon='ERROR')
        op.kind = 'ERROR'

# =========================================================
# Register
# =========================================================
classes = (
    NBPreferences,
    NBProps,
    NB_OT_Run,
    NB_OT_ToggleAuto,
    NB_OT_ResetCounter,
    NB_OT_ShowLastLog,
    NB_PT_Panel,
)

def register():
    global _NB_HANDLER_REGISTERED
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.nb_props = bpy.props.PointerProperty(type=NBProps)
    # Autoフラグを見て起動時に再登録する場合はここで判定してもOK（今回は手動Apply式）
    _NB_HANDLER_REGISTERED = False

def unregister():
    global _NB_HANDLER_REGISTERED
    # ハンドラ解除
    if _nb_on_render_write in bpy.app.handlers.render_write:
        bpy.app.handlers.render_write.remove(_nb_on_render_write)
    _NB_HANDLER_REGISTERED = False

    for c in reversed(classes):
        bpy.utils.unregister_class(c)
    del bpy.types.Scene.nb_props

if __name__ == "__main__":
    register()
