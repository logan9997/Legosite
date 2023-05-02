from requests_oauthlib import OAuth1Session

import json
import os 
import time

class Response():

    def __init__(self) -> None:
        self._base_url = "https://api.bricklink.com/api/store/v1/"
        self.configure_file_paths()
        self._keys = self.get_keys()
        self._auth = OAuth1Session(self._keys[0], self._keys[1], self._keys[2], self._keys[3])
        self._max_requests_limit = 5000
        self._reset_time = None
        self.read_request_count()


    def configure_file_paths(self):
        if os.path.exists("../my_scripts/keys.txt"):
            self._file = "../my_scripts/keys.txt"
        else:
            self._file = "my_scripts/keys.txt"

        potential_paths = [
            "requests_count.txt", "../requests_count.txt",
            "../my_scripts/requests_count.txt", "my_scripts/requests_count.txt"
        ]

        for path in potential_paths:
            if os.path.exists(path):
                self._request_count_file = path
                break


    def read_request_count(self):
        with open(self._request_count_file, "r") as file:
            content = file.read().rsplit("\n")

        self._request_count = int(content[0])
        self._recorded_time = float(content[1])
        self.exit_if_request_limit_exceeded()

    
    def exit_if_request_limit_exceeded(self):
        if self._request_count >= 5000 and time.time() - self._recorded_time < (60 * 60 * 24):
            print("DAILY REQUESTS LIMIT REACHED")
            exit()


    def get_keys(self):
        with open(self._file, "r") as keys:
            keys = keys.readlines()
            keys = [k.rstrip("\n") for k in keys]
        return keys
    

    def record_time(self):
        now = time.time()
        if now - self._recorded_time > (60 * 60 * 24):
            self._recorded_time = now
            self._request_count = 0
    

    def write_new_request_count(self):
        with open(self._request_count_file, "w") as file:
            if self._request_count == 0:
                write_time = str(time.time())
            else:
                write_time = str(self._recorded_time)

            file.write(f"{str(self._request_count)}\n{write_time}")


    def get_response_data(self, sub_url:str, **display:bool) -> dict[str]:
        display = display.get("display", False)
        response = self._auth.get(self._base_url + sub_url)   

        self._request_count += 1
        self.exit_if_request_limit_exceeded()

        #format response into dict
        self.response = json.loads(response._content.decode("utf-8"))

        if display:
            print(self.response)

        self.record_time()
        self.write_new_request_count()

        if "data" in self.response:
            return self.response["data"]
        else:
            return {"ERROR":self.response}
        
