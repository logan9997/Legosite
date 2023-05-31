from PIL import Image
from PIL import UnidentifiedImageError
from pathlib import Path
import os

def get_size():
    root_directory = Path('.')
    return sum(f.stat().st_size for f in root_directory.glob('**/*') if f.is_file())

img_folder = input('Path: ')

size_before = get_size()

for file in os.listdir(img_folder):

    if '.jpeg' in file or 'jpg' in file:
        continue

    img_path = os.path.join(img_folder, file)
    print(f'Compressing - {file}')
    try:
        img = Image.open(img_path)
        img = img.convert("P", palette=Image.ADAPTIVE, colors=256)
        img.save(img_path, optimize=True)
    except UnidentifiedImageError:
        print(f'UnidentifiedImageError - {file}')

size_after = get_size()

print(f'Size before - {size_before}\nSize after - {size_after}\nDifference - {size_before - size_after}')