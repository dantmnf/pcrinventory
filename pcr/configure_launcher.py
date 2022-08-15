from .pcrhelper import PcrHelper as _PcrHelper
import automator.launcher as _launcher
_launcher._configure('pcrhelper', _PcrHelper)
helper = _launcher.helper
