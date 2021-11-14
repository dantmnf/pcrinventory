import os
from fractions import Fraction
import time

import config
from automator import BaseAutomator

class PcrHelper(BaseAutomator):
    def on_device_connected(self):
        import imgreco
        self.vw, self.vh = imgreco.get_vwvh(self.viewport)
        if self._viewport[1] < 720 or Fraction(self._viewport[0], self._viewport[1]) < Fraction(16, 9):
            title = '设备当前分辨率（%dx%d）不符合要求' % (self._viewport[0], self._viewport[1])
            body = '需要宽高比等于或大于 16∶9，且渲染高度不小于 1080。'
            details = None
            if Fraction(self._viewport[1], self._viewport[0]) >= Fraction(16, 9):
                body = '屏幕截图可能需要旋转，请尝试在 device-config 中指定旋转角度。'
                img = self._device.screenshot()
                imgfile = os.path.join(config.SCREEN_SHOOT_SAVE_PATH, 'orientation-diagnose-%s.png' % time.strftime("%Y%m%d-%H%M%S"))
                img.save(imgfile)
                import json
                details = '参考 %s 以更正 device-config.json[%s]["screenshot_rotate"]' % (imgfile, json.dumps(self._device.config_key))
            for msg in [title, body, details]:
                if msg is not None:
                    self.logger.warn(msg)
            self.frontend.alert(title, body, 'warn', details)

    def load_addons(self):
        from .addons.inventory import InventoryAddon
        self.addon(InventoryAddon)
