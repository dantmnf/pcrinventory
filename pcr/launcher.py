from .pcrhelper import PcrHelper as _PcrHelper
import automator.launcher as _launcher
_launcher.prompt_prefix = 'pcrhelper'
_launcher._init(_PcrHelper)

from automator.launcher import *

if __name__ == '__main__':
    import sys as _sys
    _sys.exit(_launcher.main(_sys.argv))
