bl_info = {
    "name": "Nano-Banana (Gemini 2.5 Flash Image) Editor",
    "author": "あなた",
    "version": (0, 5, 0),
    "blender": (4, 3, 0),
    "location": "Image Editor > Nパネル > Nano-Banana",
    "description": (
        "Gemini 2.5 Flash Image(API)で参照×2+レンダ(最後)を編集。"
        "レンダ完了で自動実行/連番保存。ログ強化＆リミッター付"
    ),
    "category": "Image",
}
from .nano_banana_addon import register as _r, unregister as _u
from . import i18n

def register():
    i18n.register()
    _r()

def unregister():
    _u()
    i18n.unregister()
