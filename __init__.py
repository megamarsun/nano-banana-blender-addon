from nano_banana_addon import bl_info, register as _r, unregister as _u
import i18n


def register() -> None:
    i18n.register()
    _r()


def unregister() -> None:
    _u()
    i18n.unregister()

