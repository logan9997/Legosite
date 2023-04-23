from responses import *
from database import *
from misc import *
import key_updater  

import time


DB = DatabaseManagment()
RESP = Response()

def check_http_response():
    RESP = Response()

    #test a RESPonse to see if keys are outdated
    ip_test = RESP.get_response_data("items/MINIFIG/sw0001a")

    if "ERROR" in ip_test:
        new_ip = ip_test["ERROR"]["meta"]["description"].split(": ")[-1]
        print(f"Updating keys, key IP = {new_ip}")

        key_updater.update_ip(new_ip)
        print("Keys succesfully updated")

        #recall RESPonse() to pass new keys inside __init__
        RESP = Response()
        print(RESP.keys)


def update_prices():
    DB = DatabaseManagment()
    sw_ids = DB.get_all_itemIDs()

    #update keys if outdated
    check_http_response()
    recorded_ids = [_item[0] for _item in DB.get_todays_price_records()]

    for item in sw_ids:
        if item not in recorded_ids:
            print(item)

            item_info = RESP.get_response_data(f"items/MINIFIG/{item}/price")

            try:
                DB.add_price_info(item_info)
            except KeyError:
                print("ERROR -", item_info)
                break


def sub_sets():
    DB = DatabaseManagment()
    sw_ids = DB.get_all_itemIDs()

    for _item in sw_ids[:-100]:
        parts = RESP.get_RESPonse_data(f"items/MINIFIG/{_item[0]}/subsets")
        for part in parts:
            for entry in part["entries"]:
                try:
                    info = {"piece_name":entry["item"]["name"].replace("'", ""), "piece_id":entry["item"]["no"], "type":entry["item"]["type"]}
                    DB.add_pieces(info)
                    print("NEW",_item[0], entry["item"]["no"])
                except psycopg2.IntegrityError:
                    print("OLD",_item[0], entry["item"]["no"])
                
                info = {"item_id":_item[0], "piece_id":entry["item"]["no"],"colour_id":entry["color_id"], "quantity":entry["quantity"]}
                DB.add_piece_participation(info)


def super_sets():
    DB = DatabaseManagment()
    sw_ids = DB.get_all_itemIDs()

    for _item in sw_ids[:-100]:
        parts = RESP.get_RESPonse_data(f"items/MINIFIG/{_item[0]}/supersets")
        for part in parts:
            for entry in part["entries"]:
                print(_item[0],entry["item"]["no"])
                info = {"quantity":entry["quantity"], "item_id":_item[0], "set_id":entry["item"]["no"]}
                DB.add_set_participation(info)



def main():
    update_choice = input("Update: (Prices : P) (Sub Sets : SUB) (Super Sets : SUPER): ").upper()
    choices = {"P":update_prices, "SUB": sub_sets, "SUPER":super_sets}
    choices[update_choice]()


if __name__ == "__main__":
    start = time.time()
    main()
    fin = time.time()
    print(f"FINISHED IN {round(fin-start,3)} SECONDS")

