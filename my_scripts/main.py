from responses import *
from database import *
import key_updater  

import time


DB = DatabaseManagment()
RESP = Response()

def check_http_response(func):
    def inner(*args, **kwargs):
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

        func(*args, **kwargs)
    return inner


@check_http_response
def update_prices():
    DB = DatabaseManagment()
    sw_ids = DB.get_all_itemIDs()

    #update keys if outdated
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


@check_http_response
def sub_sets():
    DB = DatabaseManagment()
    sw_ids = DB.get_all_itemIDs()

    for _item in sw_ids[::-1]:
        parts = RESP.get_response_data(f"items/MINIFIG/{_item}/subsets")
        for part in parts:
            for entry in part["entries"]:
                info = {"piece_name":entry["item"]["name"].replace("'", ""), "piece_id":entry["item"]["no"], "type":entry["item"]["type"]}
                if info["piece_id"] not in DB.get_pieces():
                    DB.add_pieces(info)
                    print("-PIECES- INSERTING",entry["item"]["no"])
                    

                info = {"item_id":_item, "piece_id":entry["item"]["no"],"colour_id":entry["color_id"], "quantity":entry["quantity"]}
                if (info["piece_id"], info["item_id"]) not in DB.get_piece_participations():    
                    DB.add_piece_participation(info)
                    print("-PIECEPARTICIPATION- INSERTING", info["item_id"], info["piece_id"])


@check_http_response
def super_sets():
    DB = DatabaseManagment()
    sw_ids = DB.get_all_itemIDs()

    for _item in sw_ids:
        _sets = RESP.get_response_data(f"items/MINIFIG/{_item}/supersets")
        print(_item, _sets)
        for _set in _sets:
            for entry in _set["entries"]:
                print(_item,entry["item"]["no"])
                info = {"quantity":entry["quantity"], "item_id":_item, "set_id":entry["item"]["no"]}
                if (info["item_id"], info["set_id"]) not in DB.get_set_participations():
                    try:
                        DB.add_set_participation(info)
                    except:
                        pass


def main():
    update_choice = input("Update: (Prices : P) (Sub Sets : SUB) (Super Sets : SUPER): ").upper()
    choices = {"P":update_prices, "SUB": sub_sets, "SUPER":super_sets}
    choices[update_choice]()


if __name__ == "__main__":
    start = time.time()
    main()
    fin = time.time()
    print(f"FINISHED IN {round(fin-start,3)} SECONDS")

