import requests
import os 
import database

DB = database.DatabaseManagment()

def images():
    ids = DB.get_starwars_ids()

    for _id in ids:
        if not os.path.exists(rf"..\App\static\App\minifigures\{_id[0]}.png"):
            img = requests.get(f"https://img.bricklink.com/ItemImage/MN/0/{_id[0]}.png").content
            with open(rf"..\App\static\App\minifigures\{_id[0]}.png", "wb") as file:
                file.write(img)


if __name__ == "__main__":
    images()