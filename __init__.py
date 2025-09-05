from .nano_banana_addon import register as _r, unregister as _u
from . import i18n


def register():
    i18n.register()
    _r()


def unregister():
    _u()
    i18n.unregister()
