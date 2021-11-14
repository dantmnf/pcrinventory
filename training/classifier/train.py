import json
import os
import subprocess
import time
# from functools import lru_cache
from io import BytesIO

import cv2
import numpy as np
import torch
import torch.nn as nn
# import torch.nn.functional as F
from PIL import Image

from focal_loss import FocalLoss

collect_path = 'images/collect/'
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
if torch.cuda.is_available():
    torch.backends.cudnn.benchmark = True


def load_images():
    img_map = {}
    gray_img_map = {}
    item_id_map = {}
    img_files = []
    collect_list = os.listdir('images/collect')
    collect_list.sort()
    weights = []
    for cdir in collect_list:
        dirpath = 'images/collect/' + cdir
        sub_dir_files = os.listdir(dirpath)
        weights.append(len(sub_dir_files))
        for filename in sub_dir_files:
            filepath = os.path.join(dirpath, filename)
            with open(filepath, 'rb') as f:
                nparr = np.frombuffer(f.read(), np.uint8)
                # convert to image array
                image = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
                image = cv2.resize(image, (140, 140))
                if image.shape[-1] == 4:
                    image = image[..., :-1]
                gray_img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                gray_img_map[filepath] = gray_img
                img_files.append(filepath)
                item_id_map[filepath] = cdir
                img_map[filepath] = torch.from_numpy(np.transpose(image, (2, 0, 1)))\
                    .float().to(device)
    weights_t = torch.as_tensor(weights)
    weights_t[weights_t > 50] = 50
    weights_t = 1 / weights_t
    return img_map, gray_img_map, img_files, item_id_map, weights_t

idx2id = {}
id2idx = {}
NUM_CLASS = len(idx2id)
print('NUM_CLASS', NUM_CLASS)



def get_noise_data():
    images_np = np.random.rand(40, 64, 64, 3)
    labels_np = np.asarray(['other']).repeat(40)
    return images_np, labels_np


max_resize_ratio = 100


# @lru_cache(maxsize=10000)
# def get_resized_img(img_map, filepath, ratio):
#     img_t = img_map[filepath]
#     ratio = 1 + 0.2 * (ratio / max_resize_ratio)
#     return F.interpolate(img_t, scale_factor=ratio, mode='bilinear')


def get_data(img_files, item_id_map, img_map):
    images = []
    labels = []
    for filepath in img_files:
        item_id = item_id_map[filepath]

        t = 4 if item_id != 'other' else 1
        for _ in range(t):
            # ratio = np.random.randint(-max_resize_ratio, max_resize_ratio)
            # img_t = get_resized_img(filepath, ratio)
            img_t = img_map[filepath]
            image_aug = img_t

            images.append(image_aug)
            labels.append(id2idx[item_id])
    images_t = torch.stack(images)
    labels_t = torch.from_numpy(np.array(labels)).long().to(device)

    # print(images_np.shape)
    return images_t, labels_t


class Cnn(nn.Module):
    def __init__(self):
        super(Cnn, self).__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(3, 32, 5, stride=3, padding=2),  # 32 * 20 * 20
            nn.BatchNorm2d(32),
            nn.ReLU(True),
            nn.AvgPool2d(5, 5),  # 32 * 4 * 4
            nn.Conv2d(32, 32, 3, stride=2, padding=1),  # 32 * 2 * 2
            nn.BatchNorm2d(32),
            nn.ReLU(True),
            # nn.AvgPool2d(2, 2),
        )

        self.fc = nn.Sequential(
            nn.Linear(32 * 2 * 2, 2 * NUM_CLASS),
            nn.ReLU(True),
            nn.Linear(2 * NUM_CLASS, NUM_CLASS))

    def forward(self, x):
        x /= 255.
        out = self.conv(x)
        out = out.reshape(-1, 32 * 2 * 2)
        out = self.fc(out)
        return out


def train():
    img_map, img_files, item_id_map, weights_t = load_images()
    criterion = FocalLoss(NUM_CLASS, alpha=weights_t)
    criterion.to(device)

    def compute_loss(x, label):
        loss = criterion(x, label)
        prec = (x.argmax(1) == label).float().mean()
        return loss, prec

    print('train on:', device)
    model = Cnn().to(device)
    optim = torch.optim.Adam(model.parameters(), lr=1e-3)
    model.train()
    step = 0
    prec = 0
    target_step = 1500
    last_time = time.monotonic()
    while step < target_step or prec < 1 or step > 2*target_step:
        images_t, labels_t = get_data(img_files, item_id_map, circle_map, img_map)
        optim.zero_grad()
        score = model(images_t)
        loss, prec = compute_loss(score, labels_t)
        loss.backward()
        optim.step()
        if step < 10 or step % 50 == 0:
            print(step, loss.item(), prec.item(), time.monotonic() - last_time)
            last_time = time.monotonic()
        step += 1
    torch.save(model.state_dict(), './model.pth')
    torch.onnx.export(model, torch.rand((1, 3, 60, 60)).to(device), 'pcr_equip.onnx')


def load_model():
    model = Cnn()
    device = torch.device('cpu')
    model.load_state_dict(torch.load('./model.pth', map_location=device))
    model.eval()
    return model


def predict(model, roi_list):
    """
    Image size of 720p is recommended.
    """
    roi_np = np.stack(roi_list, 0)
    roi_t = torch.from_numpy(roi_np).float()
    with torch.no_grad():
        score = model(roi_t)
        probs = nn.Softmax(1)(score)
        predicts = score.argmax(1)

    probs = probs.cpu().data.numpy()
    predicts = predicts.cpu().data.numpy()
    return [(idx2id[idx], idx) for idx in predicts], [probs[i, predicts[i]] for i in range(len(roi_list))]


def test():
    model = load_model()
    # screen = Image.open('images/screen.png')
    screen = inventory.screenshot()
    items = inventory.get_all_item_img_in_screen(screen)
    roi_list = []
    for x in items:
        roi = x['rectangle2']
        # roi = roi / 255
        roi = np.transpose(roi, (2, 0, 1))
        roi_list.append(roi)
    res = predict(model, roi_list)
    print(res)
    for i in range(len(res[0])):
        item_id = res[0][i][0]
        idx = res[0][i][1]
        if item_id == 'other':
            print(res[1][i], 'other')
        else:
            print(res[1][i], item_id, inventory.item_map.get(item_id), idx2name[idx])
        inventory.show_img(items[i]['rectangle'])


def screenshot():
    content = subprocess.check_output('adb exec-out "screencap -p"', shell=True)
    if os.name == 'nt':
        content = content.replace(b'\r\n', b'\n')
    # with open('images/screen.png', 'wb') as f:
    #     f.write(content)
    # img_array = np.asarray(bytearray(content), dtype=np.uint8)
    return Image.open(BytesIO(content))


def save_collect_img(item_id, img):
    if not os.path.exists(collect_path + item_id):
        os.mkdir(collect_path + item_id)
    cv2.imwrite(collect_path + item_id + '/%s.png' % int(time.time() * 1000), img)


def prepare_train_resource():
    model = load_model()
    screen = inventory.screenshot()
    items = inventory.get_all_item_img_in_screen(screen)
    roi_list = []
    for x in items:
        roi = x['rectangle2'].copy()
        # roi = roi / 255
        # inventory.show_img(roi)
        roi = np.transpose(roi, (2, 0, 1))
        roi_list.append(roi)
    res = predict(model, roi_list)
    print(res)
    for i in range(len(res[0])):
        item_id = res[0][i]
        print(res[1][i], inventory.item_map[int(item_id)])
        if res[1][i] < 0.1:
            item_id = 'other'
        else:
            keycode = inventory.show_img(items[i]['rectangle2'])
            if keycode != 13:
                item_id = 'other'
        print(item_id)
        save_collect_img(item_id, items[i]['rectangle'])


def prepare_train_resource2():
    screen = inventory.screenshot()
    items = inventory.get_all_item_img_in_screen(screen, 2.15)
    for item in items:
        cv2.imwrite(f'images/manual_collect/{int(time.time() * 1000)}', item['rectangle'])


def softmax(x):
    """Compute softmax values for each sets of scores in x."""
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum(axis=0)


def test_cv_onnx():
    net = cv2.dnn.readNetFromONNX('ark_material.onnx')
    screen = Image.open('images/screen.png')
    # screen = screenshot()
    items = inventory.get_all_item_img_in_screen(screen)
    for x in items:
        roi = x['rectangle2']
        # inventory.show_img(roi)
        blob = cv2.dnn.blobFromImage(roi)
        net.setInput(blob)
        out = net.forward()

        # Get a class with a highest score.
        out = out.flatten()
        out = softmax(out)
        # print(out)
        classId = np.argmax(out)
        # confidence = out[classId]
        confidence = out[classId]
        item_id = idx2id[classId]
        print(confidence, inventory.item_map[item_id] if item_id.isdigit() else item_id)
        # inventory.show_img(x['rectangle'])


def export_onnx():
    model = load_model()
    screen = Image.open('images/screen.png')
    items = inventory.get_all_item_img_in_screen(screen)
    roi_list = []
    for x in items:
        roi = x['rectangle2'].copy()
        roi = np.transpose(roi, (2, 0, 1))
        roi_list.append(roi)
    roi_np = np.stack(roi_list, 0)
    roi_t = torch.from_numpy(roi_np).float()
    torch.onnx.export(model, roi_t, 'ark_material.onnx')


if __name__ == '__main__':
    train()
    # test()
    # prepare_train_resource()
    # prepare_train_resource2()
    # export_onnx()
    # test_cv_onnx()
    # print(cv2.getBuildInformation())