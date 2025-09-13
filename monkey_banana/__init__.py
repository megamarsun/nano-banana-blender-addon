bl_info = {
    "name": "Monkey Banana",
    "author": "Masamune Sakaki",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "Image Editor > N-panel > MonkeyBanana",
    "description": "Editing images rendered with Gemini 2.5 Flash Image (API)",
    "category": "Image",
}

from .monkey_banana_addon import register as _r, unregister as _u
from . import i18n


def register():
    i18n.register()
    _r()


def unregister():
    _u()
    i18n.unregister()
