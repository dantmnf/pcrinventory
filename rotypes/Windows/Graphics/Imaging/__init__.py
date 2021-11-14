from ctypes import c_int, c_int32

from rotypes.Windows.Foundation import IClosable
from rotypes.inspectable import IInspectable
from rotypes.idldsl import define_winrt_com_method, _static_method, runtimeclass, GUID
import rotypes.Windows.Storage.Streams


@GUID('689e0708-7eef-483f-963f-da938818e073')
class ISoftwareBitmap(IClosable, IInspectable):
    pass

class BitmapPixelFormat(c_int):
    Rgba8 = 30


class BitmapAlphaMode(c_int):
    Straight = 1


@GUID('DF0385DB-672F-4A9D-806E-C2442F343E86')
class ISoftwareBitmapStatics(IInspectable):
    pass


class SoftwareBitmap(runtimeclass, ISoftwareBitmap):
    CreateCopyWithAlphaFromBuffer = _static_method(ISoftwareBitmapStatics, 'CreateCopyWithAlphaFromBuffer')

define_winrt_com_method(ISoftwareBitmapStatics, "CreateCopyWithAlphaFromBuffer",
                        rotypes.Windows.Storage.Streams.IBuffer, BitmapPixelFormat, c_int32, c_int32, BitmapAlphaMode,
                        retval=SoftwareBitmap, vtbl=10)
