from requests_oauthlib import OAuth1Session

import json
import os 

class Response():

    def __init__(self) -> None:
        self.base_url = "https://api.bricklink.com/api/store/v1/"
        self.keys = self.get_keys()
        self.auth = OAuth1Session(self.keys[0], self.keys[1], self.keys[2], self.keys[3])

    
    def configure_file(self):
        if os.path.exists("../my_scripts/keys.txt"):
            self.file = "../my_scripts/keys.txt"
        else:
            self.file = "my_scripts/keys.txt"


    def get_keys(self):
        self.configure_file()
        with open(self.file, "r") as keys:
            keys = keys.readlines()
            keys = [k.rstrip("\n") for k in keys]
        return keys


    def get_response_data(self, sub_url:str, **display:bool) -> dict[str]:
        display = display.get("display", False)
        response = self.auth.get(self.base_url + sub_url)   
        #format response into dict
        self.response = json.loads(response._content.decode("utf-8"))

        if display:
            print(self.response)

        if "data" in self.response:
            return self.response["data"]
        else:
            return {"ERROR":self.response}


def main():

    resp = Response()
    a = resp.get_response_data(f"items/MINIFIG/sw0001a/price")
    print(a)
        
if __name__ == "__main__":
    main()