import requests
import datetime
import traceback
from math import floor
from time import sleep
from boilerplate import EventBoilerplate

class Events(EventBoilerplate):
    def __init__(self, driver):
        super().__init__(driver, "Howl")

        self.prev_messages = []

    def log(self, key, status):
        endpoint = self.flask_server + "/set"
        
        requests.post(url = endpoint, json = {
            "status": status,
            "key": key,
        })

    def local_reset(self, method, driver):
        sleep(10)
        self.matching_func(method)

    def matching_func(self, event):
        if (event == "coinflip"): return self.coinflip()

    def coinflip(self):
        print("Coinflip Scraping has begun")

        saved = False
        driver = self.driver # Make driver local

        try:
            driver.get("https://howl.gg")
        except:
            pass