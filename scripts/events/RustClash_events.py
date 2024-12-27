import requests
import datetime
import traceback
from math import floor, ceil
from time import sleep
from boilerplate import EventBoilerplate

class Events(EventBoilerplate):

    prev_messages = []
    chat_messages = []
    chat_users = []

    rakebackCount = 0
    miscIterations = 0
    onlineIterations = 0
    totalRakebackPayout = 0
    calculatedTotalOnline = 0
    totalLeaderboardWager = 0

    def __init__(self, driver):
        super().__init__(driver, "RustClash")

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
        if (event == "roulette"): return self.roulette()
        if (event == "cases"): return self.cases()

    def get_case_id(self, href):
        try: return href.split("/")[-1]
        except: return ""

    def cases(self):
        print("Cases Scraping has begun")

        driver = self.driver

        try:
            driver.get("https://rustclash.com/battles")

            cf_response = self.bypass_cloudflare(driver)

            if not cf_response:
                print("Cloudflare failed.")
                self.log(self.prefix + "Cases", False)
                sleep(30)
                return self.local_reset("cases")

            secMult = 5
            secondsOG = 300
            seconds = secondsOG

            # Cases
            totalWager = 0
            games = 0
            players = []

        except:
            print(traceback.format_exc())
            self.log(self.prefix + "Cases", False)
            self.local_reset("cases")

    def roulette(self):
        print("Roulette Scraping has begun")

        driver = self.driver

        try:
            driver.get("https://rustclash.com/roulette")

            cf_response = self.bypass_cloudflare(driver)

            if not cf_response:
                print("Cloudflare failed.")
                self.log(self.prefix + "Roulette", False)
                sleep(30)
                return self.local_reset("roulette")

            secMult = 5
            secondsOG = 120
            seconds = secondsOG

            # Roulette
            totalWager = 0
            games = 0
            players = []
            spinning = False
            calculatedRounds = 0

            while True:
                seconds -= secMult
                sleep(secMult)
                print(seconds)

                # Leaderboard
                if (seconds == secondsOG - secMult):
                    self.leaderboard(driver)
                    continue

                # Save to DB
                if seconds == 0:
                    seconds = secondsOG

                    ## Miscs
                    # Rain
                    averageRain = 0
                    if (self.rakebackCount != 0):
                        averageRain = self.totalRakebackPayout / self.rakebackCount

                    # Online User Count
                    averageUserCount = 0
                    if (self.onlineIterations != 0):
                        averageUserCount = floor(self.calculatedTotalOnline / self.onlineIterations)

                    date = datetime.datetime.now()
                    record_misc = {
                        "date": self.helpers.hour_rounder_ceil(date),
                        "rainAmount": self.rakebackCount,
                        "averageRainValue": averageRain,
                        "chatMessages": len(self.chat_messages),
                        "totalLeaderboardWager": self.totalLeaderboardWager,
                        "uniquePlayersChat": len(list(set(self.chat_users))),
                        "averageUserCount": averageUserCount,
                    }

                    # Save to DB
                    self.db.insertOne("miscs", record_misc)

                    print(date, ": (RustClash) Miscs - Saved to DB")

                    ## Roulette
                    record_roulette = {
                        "date": self.helpers.hour_rounder_ceil(date),
                        "uniquePlayers": len(players),
                        "games": games,
                        "wager": totalWager,
                    }

                    # Save to DB
                    self.db.insertOne("roulette", record_roulette)

                    print(date, ": (RustClash) Roulette - Saved to DB")

                    # Reset
                    if len(self.prev_messages) > 20: self.prev_messages = self.prev_messages[19:]
                    else: self.prev_messages = []

                    self.chat_users = []
                    self.chat_messages = []
                    self.totalRakebackPayout = 0
                    self.rakebackCount = 0
                    self.calculatedTotalOnline = 0
                    self.onlineIterations = 0

                    totalWager = 0
                    games = 0
                    players = []

                # Roulette Loop
                else:
                    betContainers = self.get_elements(
                        "#content main > div > div > div:last-child > div:nth-child(2) > div", 0
                    )

                    if not betContainers: continue
                    betContainers = list(betContainers)

                    for betContainer in betContainers:
                        betButton = self.get_from_element(betContainer, "button", 0)
                        buttonOpacity = betButton.value_of_css_property("opacity")

                        # If button opacity is 0.5, it means roulette is spinning, and it's safe to calculate
                        if buttonOpacity == "0.5" and not spinning:
                            games += 1
                            spinning = True
                            calculatedRounds += 1

                            userContainers = self.get_elements(
                                "#content main > div > div > div:last-child > div:nth-child(3) > div", 0
                            )

                            for bet in userContainers:
                                # Wager
                                wager = self.get_from_innerText(bet, "div:first-child div:last-child span", 0)
                                if not wager: continue
                                print("Wager: ", wager)
                                totalWager += float(wager)

                                # Players
                                playerEls = self.get_from_elements(bet, "div:nth-child(2) div", 0)
                                if not playerEls: continue

                                for player in playerEls:
                                    username = self.get_from_innerText(player, "span", 0)
                                    if not username: continue
                                    players.append(username)

                        elif buttonOpacity != "0.5": spinning = False

                # Misc
                if (seconds % 30 == 0):
                    self.misc()

                if (seconds % 60 == 0): self.log(self.prefix + "Roulette", True)

        except:
            print(traceback.format_exc())
            self.log(self.prefix + "Roulette", False)
            self.local_reset("roulette")

    def misc(self):
        self.miscIterations += 1
        print("Misc Iteration: ", self.miscIterations)

        try:
            # Online user count
            online = self.get_innerText("#headlessui-menu-button-:r4: > div:nth-child(2) > div")
            if online:
                self.calculatedTotalOnline += float(online)
                self.onlineIterations += 1
            print("Online user count: ", online)

            # Chat & Rakeback
            message_els = self.get_elements("div.group")

            # Chat
            for el in message_els:
                message = self.get_from_innerText(el, "div:nth-child(2) > div > span", 1)
                user = self.get_from_innerText(el, "div:first-child > span", 1)

                if not message: continue

                # Add message if it's not duplicated in previous message history
                if message not in self.prev_messages:
                    self.chat_messages.append(user)
                    self.chat_messages.append(message)
                    self.prev_messages.append(message)

            # Check rakeback rain
            section = self.get_element("section")
            raining = False

            try:
                rainingText = self.get_from_innerText(
                    section,
                    "div:first-child > div:nth-child(2) > div:first-child > div:first-child > div:first-child > div:nth-child(2) > div:nth-child(2) > span",
                    3
                )

                if not rainingText: raise Exception("Not raining")

                print(rainingText)

                if "It's about to RAIN!" in rainingText:
                    raining = True
                else:
                    raining = False
            except:
                print("Not raining")
                self.log(self.prefix + "Misc", True)

            if self.miscIterations >= 20 and raining:
                digit_els = self.get_from_elements(
                    section,
                    "div:first-child > div:nth-child(2) > div:first-child > div:first-child > div:first-child > div:nth-child(2) > div:first-child div > *",
                    3
                )

                payout = ""
                isOkay = True

                for el in digit_els:
                    # Search for separator <span>
                    if (el.get_attribute("innerText") == "."):
                        payout = payout + "."

                    # Get digit
                    else:
                        try:
                            transformX = self.get_from_element(el, "div:first-child").value_of_css_property("translateY")
                            if not transformX: isOkay = False
                            digit = ceil(float(transformX[:-1]) // 10)
                            payout = digit + payout
                        except: pass

                print("Rain payout (raw): ", payout)

                if isOkay:
                    self.totalRakebackPayout += float(payout)
                    self.rakebackCount += 1
                    raining = False
                    isOkay = True
                    self.log(self.prefix + "Misc", True)

                else: self.log(self.prefix + "Misc", False)

                self.miscIterations = 0

            print("Rain count: ", self.rakebackCount)
            print("Rain payout: ", self.totalRakebackPayout)

        except:
            print(traceback.format_exc())
            self.log(self.prefix + "Misc", False)

    def leaderboard(self, driver):
        # Leaderboard
        self.totalLeaderboardWager = 0

        try:
            # Go to the leaderboard page
            self.get_element("a[href='/race']").click()

            sleep(2)

            second_container = self.get_element("#content main > div > div > div:nth-child(4)")

            if not second_container:
                print("Containers cannot be found")
                raise Exception("Leaderboard list is empty")

            last_els = self.get_from_elements(
                second_container,
                "div:nth-child(3) div:first-child > div > div > div > span"
            )

            if not last_els:
                print("Last elements cannot be found")
                raise Exception("Leaderboard list is empty")
            
            wager = driver.execute_script(
                """
                    let wager = 0;
                    let els = document.querySelectorAll(
                        "#content main > div > div > div:nth-child(3) > div div div:last-child > div:nth-child(3) > div > span"
                    );
                    for (let el of els) wager += parseFloat(el.innerHTML.replaceAll(",", ""));
                    return wager;
                """
            )

            print(wager)

            last_els = list(last_els)

            for i in range(len(last_els)):
                try:
                    el = last_els[i]

                    # Get wager
                    wager_raw = el.get_attribute("innerText").replace(",", "")
                    if not wager_raw: continue
                    print(wager_raw)

                    wager = float(wager_raw)
                    self.totalLeaderboardWager += wager
                except:
                    print(traceback.format_exc())
                    raise Exception("Cannot calculate leaderboard wagers")

            # Go back
            self.get_element("a[href='/roulette']").click()

            print("Leaderboard wager: ", self.totalLeaderboardWager)

        except Exception as e:
            print("RAW ERROR MESSAGE: ", e)
            print(traceback.format_exc())
            self.log(self.prefix + "Misc", False)

            try: self.get_element("a[href='/roulette']").click()
            except: self.local_reset("roulette")