import cv2
import numpy as np
import imgreco.resources
from util import cvimage as Image
inventory_mask = imgreco.resources.load_image('inventory/inventory_mask.png', imread_flags=cv2.IMREAD_GRAYSCALE)
inventory_mask16 = inventory_mask.resize((16, 16), resample=Image.NEAREST).array
inventory_mask = inventory_mask.array
filenames = imgreco.resources.get_entries('inventory/icons')[1]
templates = {filename.removesuffix('.webp').removesuffix('.png'): imgreco.resources.load_image('inventory/icons/' + filename, imread_flags=cv2.IMREAD_COLOR).resize((48, 48)) for filename in filenames if filename.endswith('.webp') or filename.endswith('.png')}

all_itemid = np.array(list(templates.keys()), dtype=object)
all_icons = np.concatenate([templates[x].array[None, ...] for x in all_itemid]).astype(np.float32)
all_icons_16 = np.concatenate([templates[x].resize((16, 16)).array[None, ...] for x in all_itemid]).astype(np.float32)
all_icons[:, inventory_mask == 0] = 0
all_icons_16[:, inventory_mask16 == 0] = 0
