import requests
import os 
import database

DB = database.DatabaseManagment()

def images():
    ids = DB.get_starwars_ids()

    print(f"{len(ids)} star wars ids in database\n{ids[-1]} - last item_id to be added to database.")

    for _id in ids:
        if not os.path.exists(rf"..\App\static\App\minifigures\{_id[0]}.png"):
            print("adding", _id[0])
            img = requests.get(f"https://img.bricklink.com/ItemImage/MN/0/{_id[0]}.png").content
            with open(rf"..\App\static\App\minifigures\{_id[0]}.png", "wb") as file:
                file.write(img)

    print(os.listdir(r"..\App\static\App\minifigures"))


if __name__ == "__main__":
    images()