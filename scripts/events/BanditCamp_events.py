import requests
import datetime
import traceback
from math import floor
from time import sleep
from boilerplate import EventBoilerplate

class Events(EventBoilerplate):

    prev_messages = []

    def __init__(self, driver):
        super().__init__(driver, "BanditCamp")

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
        if (event == "misc"): return self.misc()
        if (event == "crate"): return self.crate()
        if (event == "wheel"): return self.wheel()
        if (event == "spinner"): return self.spinner()

    def parse_user_id(self, raw):
        if "steamstatic" not in raw and "imgur" not in raw: return None

        isBot = "steamstatic" not in raw
        id = ""

        if isBot: id = "bot"
        else: id = raw.split("https://avatars.steamstatic.com/")[1].split("_")[0]
            
        return { "id": id }
    
    def get_game_id(self, el):
        try: return el.get_attribute("href").split("/")[-1]
        except: return None
    
    def filter_ended_crates(self, el):
        try:
            text_el = self.get_from_element(el, "div:not(.game-info):not(.rounds)")
            winner_text = self.get_from_innerText(text_el, "h4", 0)

            if "winner" in winner_text.lower(): return True
            return False
        except:
            return False
    
    def filter_ended_spins(self, el):
        try:
            button_el = self.get_from_element(el, ".game-actions button:disabled")
            rolled_text = button_el.get_attribute("innerText")
            
            if "ROLLED" in rolled_text: return True
            return False
        except:
            return False

    def crate(self):
        print("Crate Scraping has begun")

        saved = False
        driver = self.driver # Make driver local

        try:
            driver.get("https://bandit.camp/crate-battles/")
            sleep(20)

            cf_response = self.bypass_cloudflare(driver)

            if not cf_response:
                print("Cloudflare failed.")
                self.log(self.prefix + "Crates", False)
                sleep(30)
                return self.local_reset("crate")

            secMult = 5
            secondsOG = 1200
            seconds = secondsOG

            # Crates
            totalWager = 0
            prev_ids = []
            players = []
            games = []
            ids = []

            # Set page zoom
            # Show 50 crates instead of default 10
            driver.set_script_timeout(60)
            cratesReady = driver.execute_async_script(
            """
                const done = arguments[arguments.length - 1];
                let counter = 0;
                function crates_ready() {
                    try {
                        document.querySelector("body").style.zoom = 0.18;
                        let el = document.querySelector(".game-container > div > div > div > div > button");
                        el.dispatchEvent(new MouseEvent('mouseenter', {
                            'view': window,
                            'bubbles': true,
                            'cancelable': true
                        }));
                        setTimeout(() => {
                            document.querySelector(\".v-application > .v-menu__content div[role='menuitem']:last-child\").click()
                            done(true)
                        }, 5);
                    } catch(e) {
                        if (counter > 15) done(false)
                        counter++;
                        setTimeout(crates_ready, 5000);
                    }
                }
                crates_ready()
            """)

            print("Crates response:", cratesReady)
            if not cratesReady: return self.local_reset("crates")

            while True:
                # Timer
                seconds -= secMult

                # Crate games
                if (seconds % 5 == 0):
                    try:
                        crate_elements = []
                        crate_elements_raw = self.get_elements(".battle-listing")

                        if crate_elements_raw != None:
                            crate_elements = list(filter(self.filter_ended_crates, crate_elements_raw))

                        local_players = []

                        for el in crate_elements:
                            id = self.get_game_id(el)
                            if id in ids or id == None: continue

                            # Get all users
                            avatar_els = self.get_from_elements(el, ".game-info .teams .v-avatar .v-image__image:not(.v-image__image--preload)", 3)
                            if avatar_els == None: continue

                            isBot = False
                            for avatar_el in avatar_els:
                                try:
                                    user_response = self.parse_user_id(avatar_el.get_attribute("style"))

                                    if user_response == None: continue
                                    if user_response["id"] != "bot":
                                        players.append(user_response["id"])
                                        local_players.append(user_response["id"])
                                    else: isBot = True

                                except:
                                    continue

                            ## Game stats
                            # Wager
                            wager_el = self.get_from_element(el, ".game-info > div:first-child > span:first-child > span")
                            if wager_el != None: wager = float(wager_el.get_attribute("innerText").replace(",", ""))
                            else: wager = 0

                            if not isBot: totalWager += wager

                            obj = {
                                "id": id,
                                "bot": isBot,
                                "wager": wager,
                                "local_players": local_players
                            }

                            print(obj)

                            games.append(obj)
                            ids.append(id)
                    except:
                        print(traceback.format_exc())
                        sleep(1)
                        self.log(self.prefix + "Crates", False)

                # Save to DB
                if (seconds == 0):
                    seconds = secondsOG

                    # Get DB Datas
                    stats = self.db.getOne("stats")
                    savedPlayers = stats.get("players")
                    uniquePlayers = 0

                    for i in range(len(games)):
                        game = games[i]

                        # Get unique players
                        for id in game["local_players"]:
                            if id not in savedPlayers:
                                uniquePlayers += 1

                        # Remove duplicate games
                        if game["id"] in prev_ids: continue
                        else:
                            games = games[i:]
                            ids = ids[i:]
                            break

                    if len(ids) <= 1: continue
                    if not saved: saved = True

                    ## Update crate data
                    local_realGames = []
                    local_botGames = []

                    for game in games:
                        if game["bot"]: local_botGames.append(game["id"])
                        else: local_realGames.append(game["id"])

                    date = datetime.datetime.now()
                    record = {
                        "date": self.helpers.hour_rounder_ceil(date),
                        "games": len(local_realGames),
                        "bots": len(local_botGames),
                        "wager": totalWager,
                        "uniquePlayers": uniquePlayers
                    }

                    # Players
                    if (savedPlayers == None): stats["players"] = []

                    # Merge Users
                    new_misc = list(players)
                    new_misc.extend(x for x in stats["players"] if x not in new_misc)
                    stats["players"] = new_misc

                    # Update DB and log the date
                    self.db.update("stats", {}, stats)
                    self.db.insertOne("crates", record)

                    print(date, ": (BanditCamp) Crates - Saved to DB")

                    prev_ids = ids.copy()

                    # Reset
                    ids = []
                    games = []
                    totalWager = 0

                sleep(secMult)
                if (seconds % 60 == 0): self.log(self.prefix + "Crates", True)
        except:
            print(traceback.format_exc())
            self.log(self.prefix + "Crates", False)
            self.local_reset("crate")

    def wheel(self):
        print("Wheel Scraping has begun")

        driver = self.driver # Make driver local

        try:
            driver.get("https://bandit.camp/wheel")

            cf_response = self.bypass_cloudflare(driver)

            if not cf_response:
                print("Cloudflare failed.")
                self.log(self.prefix + "Crates", False)
                sleep(30)
                return self.local_reset("wheel")

            secMult = 5
            secondsOG = 1200
            seconds = secondsOG

            # Wheel
            gamesCount = 0
            totalWager = 0
            totalPlayer = 0

            calculated = False

            while True:
                seconds -= secMult

                if (seconds % 20 == 0): calculated = False

                # Wheel Games
                if not calculated:
                    try:
                        # Check if round finished
                        self.get_element(".timer-row svg[data-icon='lock']")

                        try:
                            playerEl = self.get_elements(".player")
                            if (playerEl): totalPlayer += len(list(playerEl))
                            else: continue

                            ## Get game data
                            # Wager amount
                            strWager = self.get_innerText(".bet-interface > div:nth-child(3) h3 span:last-child > span").replace(",", "")
                            if strWager == "" or not strWager: pass
                            else: totalWager += float(strWager)

                            # User amount
                            strUser = self.get_innerText(".bet-interface > div:nth-child(3) h3 span:first-child").split(" ")[0].replace(",", "")
                            if strUser == "" or not strUser: pass
                            else: totalPlayer += float(strUser)

                            gamesCount += 1
                            calculated = True
                        except:
                            print(traceback.format_exc())
                            sleep(1)
                            self.log(self.prefix + "Wheel", False)

                    except:
                        pass

                if seconds == 0:
                    seconds = secondsOG

                    if gamesCount <= 1: continue

                    ## Update crate data
                    date = datetime.datetime.now()
                    record = {
                        "date": self.helpers.hour_rounder_ceil(date),
                        "games": gamesCount,
                        "wager": totalWager,
                        "players": totalPlayer
                    }

                    self.db.insertOne("wheels", record)

                    print(datetime.datetime.now(), ": (BanditCamp) Wheel - Saved to DB")

                    # Reset
                    gamesCount = 0
                    totalWager = 0
                    totalPlayer = 0

                sleep(secMult)
                if (seconds % 60 == 0): self.log(self.prefix + "Wheel", True)

        except:
            print(traceback.format_exc())
            self.log(self.prefix + "Wheel", False)
            self.local_reset("wheel")

    def spinner(self):
        print("Spinner Scraping has begun")
        
        driver = self.driver # Make driver local

        try:
            driver.get("https://bandit.camp/spinners")

            cf_response = self.bypass_cloudflare(driver)

            if not cf_response:
                print("Cloudflare failed.")
                self.log(self.prefix + "Crates", False)
                sleep(30)
                return self.local_reset("spinner")

            secMult = 5
            secondsOG = 1200
            seconds = secondsOG

            # Spinner
            totalWager = 0
            prev_ids = []
            players = []
            games = []
            ids = []

            # Set page zoom
            driver.execute_script("document.querySelector(\"body\").style.zoom = 0.33;")

            while True:
                seconds -= secMult

                # Spinner Games
                if (seconds % 20 == 0): # 45 Seconds
                    try:
                        # Get game containers with "ROLLED" text in it
                        # These games are finished

                        rolled_games = self.get_elements(".spinners-item")
                        if not rolled_games: rolled_games = []

                        rolled_games = list(rolled_games)
                        rolled_games = filter(self.filter_ended_spins, rolled_games)

                        for el in rolled_games:
                            obj = {}
                            spinner_ids = []
                            wagerCalculated = False

                            # Get users
                            avatar_els = self.get_from_elements(el, ".player-slots > .slot .v-avatar .v-image__image")
                            if avatar_els == None: continue

                            user_response = None

                            for avatar_el in avatar_els:
                                try:
                                    user_response = self.parse_user_id(avatar_el.get_attribute("style"))

                                    if user_response["id"] == None or user_response == None:
                                        continue

                                    if user_response["id"] != "bot":
                                        players.append(user_response["id"])
                                        spinner_ids.append(user_response["id"])

                                        if (not wagerCalculated):
                                            totalWager += wager
                                            wagerCalculated = True
                                except:
                                    continue

                            # Game ID
                            game_id = "-".join(spinner_ids)

                            if game_id in ids: continue

                            wager_el = self.get_from_element(el, ".game-total > span")
                            if not wager_el: continue
                            wager = float(wager_el.get_attribute("innerText").replace(",", ""))

                            obj = {
                                "id": game_id,
                                "wager": wager,
                            }

                            games.append(obj)
                            ids.append(game_id)

                    except:
                        print(traceback.format_exc())
                        sleep(1)
                        self.log(self.prefix + "Spinner", False)

                if seconds == 0:
                    seconds = secondsOG

                    # Get DB Datas
                    stats = self.db.getOne("stats")
                    savedPlayers = stats.get("players")

                    for i in range(len(games)):
                        game = games[i]

                        # Remove duplicate games
                        if game["id"] in prev_ids: continue
                        else:
                            games = games[i:]
                            ids = ids[i:]
                            break

                    if len(ids) <= 1: continue

                    ## Update crate data
                    date = datetime.datetime.now()
                    record = {
                        "date": self.helpers.hour_rounder_ceil(date),
                        "games": len(games),
                        "wager": totalWager,
                    }

                    # Players
                    if (savedPlayers == None): stats["players"] = []

                    # Merge Users
                    new_misc = list(players)
                    new_misc.extend(x for x in stats["players"] if x not in new_misc)
                    stats["players"] = new_misc

                    # Update DB and log the date
                    self.db.update("stats", {}, stats)
                    self.db.insertOne("spinners", record)

                    print(date, ": (BanditCamp) Spinner - Saved to DB")

                    prev_ids = ids.copy()

                    # Reset
                    ids = []
                    games = []
                    totalWager = 0

                sleep(secMult)
                if (seconds % 60 == 0): self.log(self.prefix + "Spinner", True)
        except:
            print(traceback.format_exc())
            self.log(self.prefix + "Spinner", False)
            self.local_reset("spinner")

    def misc(self):
        print("Misc Scraping has begun")

        driver = self.driver

        try:
            driver.get("https://bandit.camp/")

            cf_response = self.bypass_cloudflare(driver)

            if not cf_response:
                print("Cloudflare failed.")
                self.log(self.prefix + "Crates", False)
                sleep(30)
                return self.local_reset("misc")

            secMult = 10
            secondsOG = 1200
            seconds = secondsOG

            # Chat
            local_messages = []
            local_users = []

            # Rakeback
            totalRakebackPayout = 0
            prevRainPayout = 0
            rakebackCount = 0

            # Leaderboard
            totalLeaderboardWager = 0

            # Online users
            calculatedTotalOnline = 0
            onlineIterations = 0

            while True:
                #Timer
                seconds -= secMult

                # Leaderboard
                if (seconds == secondsOG - secMult):
                    try:
                        # Go to the leaderboard page
                        driver.execute_script("""
                            window.history.pushState({}, '', '/leaderboards');
                            window.dispatchEvent(new Event('popstate'));
                        """)

                        driver.implicitly_wait(2)
                        sleep(1)

                        els = [
                            self.get_element(".order-1"),
                            self.get_element(".order-2"),
                            self.get_element(".order-3"),
                        ]

                        last_els = self.get_elements(".page-content > div:nth-child(4) > div > div:first-child")
                        if not last_els: continue
                        last_els = list(last_els)

                        for i in range(len(last_els)):
                            try:
                                el = last_els[i]

                                # Get wager
                                if i < 3:
                                    scrapText = self.get_from_element_attribute(el, ".scrap span", "innerText").replace(",", "")
                                else:
                                    scrapText = self.get_from_element_attribute(el, "span:last-child span", "innerText").replace(",", "")

                                if not scrapText: continue

                                wager = float(scrapText.replace(",", ""))
                                totalLeaderboardWager += wager
                            except: pass

                        # Go back
                        driver.execute_script("""
                            window.history.pushState({}, '', '/');
                            window.dispatchEvent(new Event('popstate'));
                        """)

                        driver.implicitly_wait(2)
                        sleep(1)

                    except:
                        print(traceback.format_exc())
                        self.log(self.prefix + "Misc", False)
                        self.local_reset("misc")

                # Online user count
                elif (seconds % 60 == 0):
                    try:
                        online = self.get_innerText(".layout-container > div > div:nth-child(2) h4")
                        if online:
                            if online[0] == " ": online = online[1:]
                            calculatedTotalOnline += float(online.split(" ")[0].replace(",", ""))
                            onlineIterations += 1
                    except:
                        print(traceback.format_exc())
                        sleep(1)
                        self.log(self.prefix + "Misc", False)

                # Chat & Rakeback
                elif (seconds % 10 == 0):
                    # Make auto-scroll active
                    pause_banner = self.get_element(".pause-banner > div")
                    if pause_banner:
                        if pause_banner.is_enabled() and pause_banner.is_displayed():
                            pause_banner.click()

                    message_els = self.get_elements(".chat-message", 1)

                    for el in message_els:
                        # Chat
                        try:
                            message = self.get_from_element_attribute(el, ".message-content > span:last-child", "innerText", 1).replace(": ", "", 1)
                            user = self.get_from_element_attribute(el, ".message-content .username span:last-child", "innerText", 1)

                            if message:
                                # Add message if it's not duplicated in previous message history
                                if message not in self.prev_messages:
                                    local_users.append(user)
                                    local_messages.append(message)
                                    self.prev_messages.append(message)

                        except:
                            print(traceback.format_exc())
                            sleep(1)
                            self.log(self.prefix + "Misc", False)

                        # Check rakeback rain
                        try:
                            source = el.get_attribute("innerHTML")
                            if "Rakeback Rain" in source and "claimed" in source:
                                payout = self.get_from_element_attribute(el, ".scrap span", "innerText", 2)

                                if payout: payout = payout.replace(",", "")
                                if payout == prevRainPayout: continue

                                print(payout)

                                prevRainPayout = payout
                                rakebackCount += 1
                                totalRakebackPayout += float(payout)
                        except:
                            # print(traceback.format_exc())
                            pass

                # Save to DB
                if (seconds == 0):
                    seconds = secondsOG

                    # Rain
                    averageRain = 0
                    if (rakebackCount != 0):
                        averageRain = totalRakebackPayout / rakebackCount

                    # Online User Count
                    averageUserCount = 0
                    if (onlineIterations != 0):
                        averageUserCount = floor(calculatedTotalOnline / onlineIterations)

                    date = datetime.datetime.now()
                    record = {
                        "date": self.helpers.hour_rounder_ceil(date),
                        "rainAmount": rakebackCount,
                        "averageRainValue": averageRain,
                        "chatMessages": len(local_messages),
                        "totalLeaderboardWager": totalLeaderboardWager,
                        "uniquePlayersChat": len(list(set(local_users))),
                        "averageUserCount": averageUserCount,
                    }

                    # Save to DB
                    self.db.insertOne("miscs", record)

                    print(date, ": (BanditCamp) Miscs - Saved to DB")

                    # Reset
                    if len(self.prev_messages) > 20: self.prev_messages = self.prev_messages[19:]
                    else: self.prev_messages = []
                    
                    local_users = []
                    local_messages = []
                    rakebackCount = 0
                    onlineIterations = 0
                    totalRakebackPayout = 0
                    totalLeaderboardWager = 0
                    calculatedTotalOnline = 0

                sleep(secMult)
                if (seconds % 60 == 0): self.log(self.prefix + "Misc", True)
        except:
            print(traceback.format_exc())
            self.log(self.prefix + "Misc", False)
            self.local_reset("misc")