from responses import *
from database import *
from misc import *
import key_updater  

import time

#last update 12:43 -> 12:55

db = DatabaseManagment()
resp = Response()

def check_http_response():
    resp = Response()

    #test a response to see if keys are outdated
    ip_test = resp.get_response_data("items/MINIFIG/sw0001a")

    if "ERROR" in ip_test:
        new_ip = ip_test["ERROR"]["meta"]["description"].split(": ")[-1]
        print(f"Updating keys, key IP = {new_ip}")

        key_updater.update_ip(new_ip)
        print("Keys succesfully updated")

        #recall Response() to pass new keys inside __init__
        resp = Response()
        print(resp.keys)


def update_items():

    ids = db.get_all_itemIDs()[:4500]

    for _id in ids:
        print(_id[0])
        
        info = resp.get_response_data(f"items/MINIFIG/{_id[0]}")
        if info == {}:
            info = resp.get_response_data(f"items/SET/{_id[0]}")

        print(info)
        try:
            db.insert_item_info(info)
        except sqlite3.IntegrityError or KeyError:
            print(info)
            break


def update_prices():
    DB = DatabaseManagment()
    sw_ids = db.get_all_itemIDs()

    #update keys if outdated
    check_http_response()
    recorded_ids = [_item[0] for _item in DB.get_todays_price_records()]

    for item in sw_ids:
        if item[0] not in recorded_ids:
            print(item[0])

            item_info = resp.get_response_data(f"items/MINIFIG/{item[0]}/price")

            try:
                db.add_price_info(item_info)
            except KeyError:
                print("ERROR -", item_info)
                break


def remove_sql_chars(string:str):
    return string.replace("'", "")


def sub_sets():
    DB = DatabaseManagment()
    sw_ids = db.get_all_itemIDs()

    for _item in sw_ids[:-100]:
        parts = resp.get_response_data(f"items/MINIFIG/{_item[0]}/subsets")
        for part in parts:
            for entry in part["entries"]:
                try:
                    info = {"piece_name":remove_sql_chars(entry["item"]["name"]), "piece_id":entry["item"]["no"], "type":entry["item"]["type"]}
                    DB.add_pieces(info)
                    print("NEW",_item[0], entry["item"]["no"])
                except sqlite3.IntegrityError:
                    print("OLD",_item[0], entry["item"]["no"])
                info = {"item_id":_item[0], "piece_id":entry["item"]["no"],"colour_id":entry["color_id"], "quantity":entry["quantity"]}
                DB.add_piece_participation(info)


def super_sets():
    DB = DatabaseManagment()
    sw_ids = db.get_all_itemIDs()

    for _item in sw_ids[:-100]:
        parts = resp.get_response_data(f"items/MINIFIG/{_item[0]}/supersets")
        for part in parts:
            for entry in part["entries"]:
                print(_item[0],entry["item"]["no"])
                info = {"quantity":entry["quantity"], "item_id":_item[0], "set_id":entry["item"]["no"]}
                DB.add_set_participation(info)



def main():
    update_prices()

if __name__ == "__main__":
    start = time.time()
    main()
    fin = time.time()
    print(f"FINISHED IN {round(fin-start,3)} SECONDS")

