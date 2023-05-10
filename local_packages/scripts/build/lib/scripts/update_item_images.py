import requests
import os 
import database

DB = database.DatabaseManagment()

def images():

    item_type = input("Type, M / S").upper()

    type_convert = {
        "M" : {
            "ids":DB.get_starwars_ids(),
            "path":"minifigures"
        },
        "S" : {
            "ids":DB.get_theme_sets("Star_Wars"),
            "path":"sets"
        }
    }

    ids = type_convert[item_type]["ids"]

    for _id in ids:
        if not os.path.exists(rf"..\App\static\App\{type_convert[item_type]['path']}\{_id}.png"):
            request_string = f"https://img.bricklink.com/ItemImage/{item_type}N/0/{_id}.png"
            print("adding", _id, request_string)
            img = requests.get(request_string).content
            with open(rf"..\App\static\App\{type_convert[item_type]['path']}\{_id}.png", "wb") as file:
                file.write(img)



if __name__ == "__main__":
    images()