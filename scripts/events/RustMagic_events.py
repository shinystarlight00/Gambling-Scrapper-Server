import requests
import datetime
import traceback
from time import sleep
from boilerplate import EventBoilerplate

class Events(EventBoilerplate):
    def __init__(self, driver):
        super().__init__(driver, "RustMagic")

        self.prev_messages = []

    def log(self, key, status):
        endpoint = self.flask_server + "/set"
        
        requests.post(url = endpoint, json = {
            "status": status,
            "key": key,
        })

    def local_reset(self, method):
        sleep(10)
        self.matching_func(method)

    def matching_func(self, event):
        if (event == "live"): return self.live()

    def live(self):
        print("Live Scraping has begun")
        
        saved = False
        driver = self.driver # Make driver local

        try:
            driver.get("https://rustmagic.com/")

            cf_response = self.bypass_cloudflare(driver)

            if not cf_response:
                print("Cloudflare failed.")
                self.log(self.prefix + "Live", False)
                sleep(30)
                return self.local_reset("live")

            driver.execute_script("location.reload()")

            sleep(5)

            driver.execute_script("""
                let container = document.querySelector("#scrollable-content-wrapper");
                container.scrollTo(0, container.scrollHeight - 1200);
            """)

            secMult = 5
            secondsOG = 120
            seconds = secondsOG

            # Live Bets
            ids = []
            games = {}

            while True:
                # Timer
                seconds -= secMult

                # Get data
                games_container = self.get_elements(
                    "#scrollable-content-wrapper > div:nth-child(4) > div:last-child > div:last-child > div",
                    3
                )

                if not games_container:
                    sleep(5)
                    print("Games Container cannot be found")
                    self.local_reset("live")

                games_container = list(games_container)

                for game_container in games_container:
                    game = self.get_from_innerText(game_container, "div:nth-child(2)", 0)
                    user = self.get_from_innerText(game_container, "div:first-child > div", 0)
                    single_wager = self.get_from_innerText(game_container, "div:nth-child(3)", 0)
                    single_payout = self.get_from_innerText(game_container, "div:nth-child(6)", 0)

                    if (not user) or (not game) or (not single_payout) or (not single_wager): continue
                    if single_payout[0] == "+": single_payout = single_payout[1:]
                    id = user + "|" + game + "|" + single_wager + "|" + single_payout
                    if id in ids: continue

                    single_payout = float(single_payout)
                    single_wager = float(single_wager)

                    if game not in games.keys():
                        games[game] = {
                            "wager": single_wager,
                            "payout": single_payout,
                            "games": 1
                        }

                    else:
                        games[game]["wager"] += single_wager
                        games[game]["payout"] += single_payout
                        games[game]["games"] += 1

                    ids.append(id)

                # Save to DB
                if (seconds == 0):
                    date = datetime.datetime.now()

                    if len(games.keys()) == 0:
                        print(date, ": (RustMagic) No game found")

                    for game in games.keys():
                        record = {
                            "date": self.helpers.hour_rounder_ceil(date),
                            "payout": games[game]["payout"],
                            "wager": games[game]["wager"],
                            "games": games[game]["games"],
                            "game": game,
                        }

                        self.db.insertOne("lives", record)

                    print(date, ": (RustMagic) Live - Saved to DB")

                    ids = []
                    games = {}
                    seconds = secondsOG

                sleep(secMult)
                if (seconds % 60 == 0): self.log(self.prefix + "Live", True)

        except:
            print(traceback.format_exc())
            self.log(self.prefix + "Live", False)
            self.local_reset("live")