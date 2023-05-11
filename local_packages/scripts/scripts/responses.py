from requests_oauthlib import OAuth1Session

import json
import time

from project_utils.environment_manager import Manager 
from project_utils.general import General

class Response():

    def __init__(self) -> None:
        self.base_url = "https://api.bricklink.com/api/store/v1/"
        self.keys = Manager().get_env_varaibles(
            'CONSUMER_KEY', 'CONSUMER_SECRET', 'TOKEN_VALUE', 'TOKEN_SECRET'
        )

        self.auth = OAuth1Session(
            self.keys['CONSUMER_KEY'], self.keys['CONSUMER_SECRET'], 
            self.keys['TOKEN_VALUE'], self.keys['TOKEN_SECRET']
        )
        self.request_count_file ='requests_count.txt'
        self.max_requests_limit = 5000
        self.reset_time = None
        self.read_request_count()



    def read_request_count(self):
        with open(self.request_count_file, "r") as file:
            content = file.read().rsplit("\n")

        self.request_count = int(content[0])
        self.recorded_time = float(content[1])
        self.exit_if_request_limit_exceeded()

    
    def exit_if_request_limit_exceeded(self):
        if self.request_count >= 5000 and time.time() - self.recorded_time < (60 * 60 * 24):
            print(f"DAILY REQUESTS LIMIT REACHED\nCounter reset in {(time.time() - self.recorded_time) / (60 * 60)} hours")
            exit()


    def record_time(self):
        now = time.time()
        if now - self.recorded_time > (60 * 60 * 24):
            self.recorded_time = now
            self.request_count = 0
    

    def write_new_request_count(self):
        with open(self.request_count_file, "w") as file:
            if self.request_count == 0:
                write_time = str(time.time())
            else:
                write_time = str(self.recorded_time)

            file.write(f"{str(self.request_count)}\n{write_time}")


    def get_response_data(self, sub_url:str, **display:bool) -> dict[str]:
        display = display.get("display", False)
        response = self.auth.get(self.base_url + sub_url)   

        self.request_count += 1
        self.exit_if_request_limit_exceeded()

        #format response into dict
        self.response = json.loads(response.content.decode("utf-8"))

        if display:
            print(self.response)

        self.record_time()
        self.write_new_request_count()

        if "data" in self.response:
            return self.response["data"]
        else:
            return {"ERROR":self.response}
        
