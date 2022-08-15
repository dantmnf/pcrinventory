from random import randint
import math
from collections import OrderedDict
from time import sleep
import time
import cv2
import numpy as np
from automator import AddonBase, cli_command
from util import cvimage as Image
from util import richlog
import imgreco.imgops
import imgreco.ocr
import imgreco.ocr.tesseract

logger = richlog.get_logger(__name__)

def crop_inventory(screenshot: Image.Image):
    vw, vh = screenshot.width / 100, screenshot.height / 100
    equip_area_top = int(round(12.917*vh))
    # equip_area_left = int(round(50*vw-80.000*vh))
    equip_area: Image.Image = screenshot.crop((50*vw-80.000*vh, 12.917*vh, 50*vw+17.778*vh, 84.954*vh))
    cols = [
        (50*vw-80.000*vh, 50*vw-62.222*vh),
        (50*vw-60.000*vh, 50*vw-42.222*vh),
        (50*vw-40.000*vh, 50*vw-22.222*vh),
        (50*vw-20.000*vh, 50*vw-2.222*vh),
        (50*vw, 50*vw+17.778*vh),
    ]
    equip_box_size = int(round(17.778*vh))
    sum_on_y = np.sum(equip_area.convert('L').array, 1, dtype=np.float32)
    equip_y = np.uint8(sum_on_y < sum_on_y.max() * 0.98).reshape(-1, 1)
    ctrs, _ = cv2.findContours(equip_y, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    rects = [cv2.boundingRect(ctr) for ctr in ctrs]
    equip_icon_pos = [(x[1], x[3]) for x in rects]  # [(y, height)]
    equip_icon_pos.sort(key=lambda x: x[0])
    result = []
    for y, height in equip_icon_pos:
        if y == 0:
            continue
        screen_y = equip_area_top + y
        for left, right in cols:
            equip_icon = screenshot.crop((left, screen_y, right, screen_y + height))
            ratio = equip_icon.height / equip_icon.width
            if 0.985 <= ratio <= 1.015:
                result.append(equip_icon)
    return result


def batch_compare_mse(roi, stacked_templates):
    all_diff = stacked_templates - roi
    np.square(all_diff, out=all_diff)
    all_mse = np.average(all_diff, axis=tuple(range(len(all_diff.shape)))[1:])
    return all_mse

def recognize_item(icon: Image.Image, vh):
    from .inventory_cache import inventory_mask, all_itemid, all_icons_16, all_icons
    masked_icon = icon.resize((48, 48))
    masked_icon.array[inventory_mask == 0] = [0, 0, 0]
    icon16 = masked_icon.resize((16, 16))
    comp16 = batch_compare_mse(icon16.array, all_icons_16)
    min16 = np.min(comp16)
    match_idx = np.where(comp16 <= (min16 * 2))[0]
    if len(match_idx) == 0:
        comparisions = [('999999', 114514)]
    else:
        # print("1st stage match:", match_idx)
        second_match_ids = all_itemid[match_idx]
        second_match_icons = all_icons[match_idx]
        comp = batch_compare_mse(masked_icon.array, second_match_icons)
        comparisions = list(zip(second_match_ids, comp))
    # for equipid, template in templates.items():
    #     template = template.copy()
    #     template.array[inventory_mask == 0] = [0, 0, 0]
    #     comparisions.append((equipid, imgreco.imgops.compare_mse(masked_icon, template)))
    # print("2nd stage match:", comparisions)
    comparisions.sort(key=lambda x:x[1])

    icon4qty = icon.convert('L')
    img4qty = icon4qty.crop((0, int(round(149/193*icon.height)), icon.width, int(round(179/193*icon.height))))
    _, th_img4qty = cv2.threshold(img4qty.array, 160, 255, cv2.THRESH_BINARY_INV)

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(th_img4qty)
    for i, (x, y, w, h, area) in enumerate(stats):
        remove_contour = False
        if x == 0 or y == 0 or x+w >= img4qty.width-1 or y+h > img4qty.height-1:
            # 在图像边缘的连通域
            remove_contour = True
        elif h < img4qty.height * 0.5 or y > img4qty.height * 0.3 or y+h < img4qty.height * 0.7:
            # 不在文字位置（垂直）的连通域
            remove_contour = True
        # elif area <= (math.sqrt(7)/1080*vh*100) ** 2:
        #     # 小面积连通域
        #     remove_contour = True
        if remove_contour:
            th_img4qty[labels == i] = 0
            # img4qty.array[labels == i] = 255

    ctr, h = cv2.findContours(th_img4qty, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for idx, c in enumerate(ctr):
        x, y, w, h = cv2.boundingRect(c)
        if x == 0 or y == 0 or x+w >= img4qty.width-1 or y+h > img4qty.height-1 or y > img4qty.height * 0.3 or y+h < img4qty.height * 0.7 or cv2.contourArea(c) <= (math.sqrt(7)/1080*vh*100) ** 2:
            cv2.drawContours(img4qty.array, ctr, idx, 255, -1)
    mask = cv2.dilate(th_img4qty, np.ones((3, 3), np.uint8), iterations=1)
    img4qty.array[mask == 0] = 255
    cropbox_img4qty = imgreco.imgops.cropbox_blackedge2(Image.fromarray(th_img4qty, 'L'), x_threshold=img4qty.height)
    if cropbox_img4qty:
        img4qty = img4qty.crop(cropbox_img4qty)
        img4qty = Image.fromarray(cv2.copyMakeBorder(img4qty.array, 8, 8, 8, 8, cv2.BORDER_CONSTANT, value=255), 'L')
    # img4qty = imgreco.imgops.enhance_contrast(img4qty, 64, 160)
    return *comparisions[0], img4qty



class InventoryAddon(AddonBase):
    def on_attach(self):
        self.tesseract: imgreco.ocr.OcrEngine = imgreco.ocr.tesseract.Engine(lang=None, model_name='pcr_nums')

    def get_inventory_items(self):
        vw, vh = self.vw, self.vh
        items = OrderedDict()
        stall_count = 0
        while True:
            last_itemids = list(items.keys())
            screenshot = self.control.screenshot().convert('BGR')
            t0 = time.perf_counter()
            item_icons = crop_inventory(screenshot)
            for icon in item_icons:
                t10 = time.perf_counter()
                itemid, score, qtyimg = recognize_item(icon, vh)
                t11 = time.perf_counter()
                logger.logtext(f"Recognize item {itemid} with score {score} in {t11-t10:.3f}s")
                if score > 1000:
                    logger.logimage(icon)
                    logger.logtext(f'nearest match {itemid} with score {score}')
                    continue
                qtystr = self.tesseract.recognize(qtyimg, hints=[imgreco.ocr.OcrHint.SINGLE_LINE], char_whitelist='×0123456789').text.replace(' ', '')
                cross_pos = qtystr.rfind('×')
                if cross_pos != -1:
                    qtystr = qtystr[cross_pos + 1:]
                qty = int(qtystr) if qtystr else -1
                logger.logimage(icon)
                logger.logimage(qtyimg)
                logger.logtext(f'matched {itemid} with score {score}, qty {qty}')
                if qty > 0:
                    items[itemid] = qty
            current_itemids = list(items.keys())
            t1 = time.perf_counter()
            logger.logtext(f'page recognized in {t1-t0:.3f}s')
            new_itemids = current_itemids[len(last_itemids):]
            if new_itemids:
                stall_count = 0
                self.logger.info('new: %r', [(newid, items[newid]) for newid in new_itemids])
            else:
                stall_count += 1
                if stall_count == 2:
                    break
            
            swipe0 = [50*vw-30.833*vh, 60.556*vh]
            swipe1 = [50*vw-30.833*vh, 27.130*vh]
            swipe0[0] += randint(int(-5*vh), int(5*vh))
            swipe1[0] += randint(int(-5*vh), int(5*vh))
            yoffset = randint(int(-5*vh), int(5*vh))
            swipe0[1] += yoffset
            swipe1[1] += yoffset
            self.control.input.touch_swipe(*swipe0, *swipe1, move_duration=0.3, hold_before_release=0.2)
            sleep(0.3)
        self.logger.info('done')

        return items

    @cli_command('inventory')
    def cli_inventory(self, argv):
        """inventory
        仓库识别。
        需要进入仓库画面并滚动到最顶端。需要宽高比不小于 16:9，高度不小于 720，且游戏显示没有黑边。"""
        items = self.get_inventory_items()
        for itemid, qty in items.items():
            print(itemid, qty)
