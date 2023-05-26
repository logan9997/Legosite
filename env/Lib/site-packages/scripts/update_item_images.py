import os

import requests
from scripts.database import DB


def images():

    item_type = input('Type, M / S').upper()

    type_convert = {
        'M': {
            'ids': DB.get_starwars_ids(),
            'path': 'minifigures'
        },
        'S': {
            'ids': DB.get_theme_sets('Star_Wars'),
            'path': 'sets'
        },
        'P': {
            'ids':DB.get_piece_id_and_colour(),
            'path': 'pieces'
        }
    }

    ids = type_convert[item_type]['ids']

    for _id in ids:
        if not os.path.exists(rf'..\legosite\App\static\App\{type_convert[item_type]["path"]}\{_id}.png'):
            if item_type != 'P':
                request_string = f'https://img.bricklink.com/ItemImage/{item_type}N/0/{_id}.png'
            else:
                request_string = f'https://img.bricklink.com/ItemImage/{item_type}N/{_id[1]}/{_id[0]}.png'

            print('adding', _id, request_string)
            img = requests.get(request_string).content
            with open(rf'..\legosite\App\static\App\{type_convert[item_type]["path"]}\{_id[0]}.png', 'wb') as file:
                file.write(img)


if __name__ == '__main__':
    images()
