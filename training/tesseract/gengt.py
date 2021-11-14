import sys
import cv2
import numpy as np
from PIL import ImageFont
import random
import os

def genimg(font, text):
    fontmask = font.getmask(text, 'L')
    mat = 255 - np.asarray(fontmask).reshape(fontmask.size[::-1])
    mat = cv2.copyMakeBorder(mat, 16, 16, 16, 16, cv2.BORDER_CONSTANT, value=255)
    noise = np.int16(np.random.normal(0, 3, mat.shape))
    mat = np.uint8(np.clip(np.int16(mat) + noise, 0, 255))
    if random.randint(0, 9) < 3:
        threshold = random.randint(100,200)
        mat[mat < threshold] = 0
        mat[mat > threshold] = 255
    return mat

def main():
    _, fontfile, fontsize, prefix, outdir = sys.argv
    fontsize = int(fontsize)
    font = ImageFont.truetype(fontfile, fontsize)
    alphabet = '×0123456789'
    for i in range(1000):
        text = ''.join(random.choice(alphabet) for x in range(80))
        img = genimg(font, text)
        imgpath = os.path.join(outdir, '%s-%06d.png' % (prefix, i))
        gtpath = os.path.join(outdir, '%s-%06d.gt.txt' % (prefix, i))
        cv2.imwrite(imgpath, img)
        with open(gtpath, 'w') as f:
            f.write(text)

if __name__ == '__main__':
    main()
