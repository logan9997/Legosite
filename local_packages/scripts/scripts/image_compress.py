from PIL import Image
from PIL import UnidentifiedImageError
import os

img_folder = input('Path: ')


for file in os.listdir(img_folder):
    img_path = os.path.join(img_folder, file)
    print(f'Compressing - {file}')
    try:
        img = Image.open(img_path)
        img = img.convert("P", palette=Image.ADAPTIVE, colors=256)
        img.save(img_path, optimize=True)
    except UnidentifiedImageError:
        print(f'UnidentifiedImageError - {file}')