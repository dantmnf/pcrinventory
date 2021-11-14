import cv2
import imgreco.resources

inventory_mask = imgreco.resources.load_image('inventory/inventory_mask.png', imread_flags=cv2.IMREAD_GRAYSCALE).array
filenames = imgreco.resources.get_entries('inventory/icons')[1]
templates = {filename[:-4]: imgreco.resources.load_image('inventory/icons/' + filename, imread_flags=cv2.IMREAD_COLOR).resize((48, 48)) for filename in filenames if filename.endswith('.png')}
