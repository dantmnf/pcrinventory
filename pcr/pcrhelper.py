import os
from fractions import Fraction
import time

import app
from automator import BaseAutomator

class PcrHelper(BaseAutomator):
    def on_device_connected(self):
        if self.viewport[1] < 720 or Fraction(self.viewport[0], self.viewport[1]) < Fraction(16, 9):
            title = '设备当前分辨率（%dx%d）不符合要求' % (self.viewport[0], self.viewport[1])
            body = '需要宽高比等于或大于 16∶9，且渲染高度不小于 1080。'
            self.frontend.alert(title, body, 'warn')

    def load_addons(self):
        from .addons.inventory import InventoryAddon
        self.addon(InventoryAddon)
