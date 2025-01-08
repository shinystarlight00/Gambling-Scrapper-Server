import datetime
import requests
import traceback
from time import sleep
from math import floor, ceil
from boilerplate import EventBoilerplate

class Events(EventBoilerplate):

    playersCount = 0

    def __init__(self, driver):
        super().__init__(driver, "RustyPot")

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
        if (event == "coinflip"): return self.RustyPot_coinflip()
        if (event == "jackpot"): return self.RustyPot_jackpot()

    def parse_game_id(self, raw):
        raw = raw.split("('")[1]
        raw = raw.split("')")[0]
        return raw

    def parse_steam_id(self, raw):
        return raw.split("/")[-1]

    def RustyPot_coinflip(self):
        print("Coinflip Scraping has begun")

        try:
            driver = self.driver # Make driver local
            driver.get("https://rustypot.com/coinflip")

            sleep(20)
            cf_response = self.bypass_cloudflare(driver)

            if not cf_response:
                print("Cloudflare failed.")
                self.log(self.prefix + "Coinflip", False)
                sleep(30)
                return self.RustyPot_coinflip()

            driver.implicitly_wait(30)

            secMult = 10
            secondsOG = 1200
            seconds = secondsOG

            ## Return Datas
            # COINFLIP
            cancelledGames = 0
            jimmyWonGames = 0
            playedGames = 0
            totalWager = 0
            botGames = 0
            wager = 0
            games = []
            users = []
            prevActiveIDs = []

            while True:
                # Timer
                seconds -= secMult

                # Coinflip Datas
                if (seconds % 60 == 0):
                    self.log(self.prefix + "Coinflip", True)

                    # Get Past Coinflip Games
                    driver.implicitly_wait(5)

                    # Get IDs of first n games
                    elementIDs = []
                    for i in range(10):
                        elementIDs.append(self.get_element_attribute("#cfHistoryCoins .cfHistoryCoin:nth-child({})".format(i + 1), "id"))

                    for i in range(10):
                        try:
                            _id = elementIDs[i]
                            conflict = False

                            for game in games:
                                if _id == game["id"]:
                                    conflict = True
                                    break

                            if conflict: break

                            # Open Game History Modal
                            driver.execute_script("viewActiveLobby('{}')".format(_id))

                            # Get Coinflip Datas
                            driver.implicitly_wait(2)

                            opponentWager_raw = self.get_innerText(".OppoentInfo .total")
                            creatorWager_raw = self.get_innerText(".CreatorInfo .total")

                            if not opponentWager_raw or not creatorWager_raw:
                                continue

                            opponentWager = float(opponentWager_raw[1:])
                            creatorWager = float(creatorWager_raw[1:])
                            wager = opponentWager + creatorWager

                            # Get Players
                            playersEl = [self.get_element(".opponent-name > a"), self.get_element(".creator-name > a")]
                            
                            jimmy = False
                            jimmyWon = False

                            for playerEl in playersEl:
                                # Get Steam ID
                                playerID = self.parse_steam_id(playerEl.get_attribute("href"))
                                opponentName = self.get_innerText(".opponent-name > a > p")

                                if opponentName == "JIMMY": jimmy = True
                                elif playerID not in users:
                                    try:
                                        int(playerID)
                                        self.playersCount += 1
                                        users.append(playerID)
                                    except: pass

                            # Determine the winner
                            if jimmy:
                                landingCoin = self.get_element_attribute("#fliper-coin .flipper", "style")
                                landedOn = ""
                                if "1620" in landingCoin: landedOn = "red"
                                elif "1800" in landingCoin: landedOn = "black"

                                creatorChoice = self.get_element_attribute(".creator-imgs img.pick", "src")

                                if ("Red" in creatorChoice and landedOn == "red") or ("Black" in creatorChoice and landedOn == "black"):
                                    jimmyWon = False
                                else:
                                    jimmyWon = True

                            # Add to Coinflip Games History
                            obj = {
                                "id": _id,
                                "wager": wager,
                            }

                            if jimmy: obj["jimmyWon"] = jimmyWon

                            games.append(obj)

                            # Close the modal
                            sleep(1)
                            driver.execute_script("$('#coinflipGame').modal('hide'); $('.modal-backdrop').remove()") 
                        except:
                            print(traceback.format_exc())
                            self.log(self.prefix + "Coinflip", False)
                            driver.execute_script("$('#coinflipGame').modal('hide'); $('.modal-backdrop').remove()")

                # Check for cancelled games
                elif seconds % 10 == 0:
                    activeIDs = []
                    endedIDs = []

                    # Get active and ended game's IDs
                    activeGames = self.get_elements(".ActiveCoinflips .coinflip")
                    if activeGames:
                        try:
                            for game in activeGames:
                                local_coinflipID = game.get_attribute("coinflip-id")

                                if not local_coinflipID:
                                    continue

                                activeIDs.append(local_coinflipID)

                            if len(prevActiveIDs) == 0: prevActiveIDs = activeIDs.copy()
                        except:
                            print(traceback.format_exc())

                        try:
                            endedGames = self.get_elements(".EndedCoinFlips .coinflip")
                            if endedGames:
                                for game in endedGames:
                                    endedIDs.append(game.get_attribute("coinflip-id"))
                        except: pass

                        # Check differences between active and previous active IDs
                        for ID in prevActiveIDs:
                            if (ID not in activeIDs) and (ID not in endedIDs):
                                cancelledGames += 1

                        prevActiveIDs = activeIDs.copy()

                # Save Datas to DB
                if (seconds == 0):
                    seconds = secondsOG

                    date = datetime.datetime.now()

                    # Get DB Datas
                    stats = self.db.getOne("stats")

                    ## Update Coinflip Datas
                    lastCoinflips_raw = self.db.getLastN("coinflips", ceil(secondsOG / 45) * 10, "games")
                    lastCoinflips = []

                    for j in lastCoinflips_raw:
                        for k in j["games"]:
                            lastCoinflips.append(k)

                    games = list(filter(lambda x: x["id"] not in lastCoinflips, games))
                    if len(games) == 0: continue
                    
                    # Get replaced IDs
                    ids = []

                    for game in games:
                        ids.append(game["id"])
                        playedGames += 1
                        localWager = game["wager"]
                        totalWager += localWager
                        if (game.get("jimmyWon") != None):
                            if (game["jimmyWon"]): jimmyWonGames += 1
                            botGames += 1

                    gamesBlock = {
                        "games": ids,
                        "bots": botGames,
                        "wager": totalWager,
                        "jimmy": jimmyWonGames,
                        "cancelled": cancelledGames,
                        "date": self.helpers.hour_rounder_ceil(date),
                    }

                    ## Update Misc Datas
                    # Merge Users
                    if (stats.get("players") == None): stats["players"] = []
                    new_misc = list(users)
                    new_misc.extend(x for x in stats["players"] if x not in new_misc)
                    stats["players"] = new_misc

                    # Update DB and log the date
                    self.db.update("stats", {}, stats)
                    if (len(games) > 0): self.db.insertOne("coinflips", gamesBlock)

                    print(date, ": (RustyPot) Coinflip - Saved to DB")

                    ## Reset local storage variables
                    # COINFLIP
                    cancelledGames = 0
                    jimmyWonGames = 0
                    playedGames = 0
                    totalWager = 0
                    botGames = 0
                    wager = 0
                    games = []
                    ids = []

                    # Refetch stats
                    stats = self.db.getOne("stats")

                sleep(secMult)

        except:
            print(traceback.format_exc())
            self.log(self.prefix + "Coinflip", False)
            self.local_reset("coinflip")

    def RustyPot_jackpot(self):
        print("Jackpot Scraping has begun")

        try:
            driver = self.driver # Make driver local
            driver.get("https://rustypot.com/")

            sleep(20)
            cf_response = self.bypass_cloudflare(driver)

            if not cf_response:
                print("Cloudflare failed.")
                self.log(self.prefix + "Jackpot", False)
                sleep(30)
                return self.RustyPot_jackpot()

            secMult = 5
            secondsOG = 1200
            seconds = secondsOG

            ## Return datas
            # MISC
            self.prevChatMessages = []
            self.savedMessages = []
            chatMessages = 0
            totalUserCount = 0
            lastFgPrice = 0
            flashGiveaways = 0
            flashGiveawayPayout = 0
            averageUserCount = { "count": 0, "iterations": 1 }

            # JACKPOT
            totalWager = 0
            playedGames = 0
            biggestGame = 0
            games = []
            users = []

            while True:
                # Timer
                seconds -= secMult

                if (seconds % 60 == 0): self.log(self.prefix + "Jackpot", True)

                # Jackpot Datas
                jackpotGameDelay = 50
                if self.node_env == "production": jackpotGameDelay = 600

                if (seconds % jackpotGameDelay == 0 and seconds != 0):
                    # Get Past Jackpot Games
                    sleep(2)

                    for i in range(5):
                        try:
                            # Check if game is new
                            el = self.get_element("#jackpotHistory .gameHistory:nth-child({})".format(i + 1))
                            if not el: break

                            _id = self.parse_game_id(el.get_attribute("onclick"))
                            conflict = False

                            for game in games:
                                if _id == game["id"]:
                                    conflict = True
                                    break

                            if (conflict): break

                            # Open Game History Modal
                            el.click()
                            # sleep(1)

                            # Get Jackpot Datas
                            wager = float(self.get_innerText(".jackpotHistoryWinner > p > span:nth-child(2)")[1:])

                            # Get Players
                            playersEl = self.get_elements(".jackpotHistoryDeposit .jackpotHistoryDepositHeader > p a")

                            for playerEl in playersEl:
                                # Get Steam ID
                                playerID = self.parse_steam_id(playerEl.get_attribute("href"))
                                if playerID not in users:
                                    self.playersCount += 1
                                    users.append(playerID)

                            # Add to Jackpot Games History
                            games.append({
                                "id": _id,
                                "wager": wager,
                            })

                            # Close the modal
                            sleep(1)
                            driver.execute_script("$('#jackpotGameHistory').modal('hide'); $('.modal-backdrop').remove()")
                        except:
                            print(traceback.format_exc())
                            sleep(1)
                            self.log(self.prefix + "Jackpot", False)
                            driver.execute_script("$('#jackpotGameHistory').modal('hide'); $('.modal-backdrop').remove()")

                # Misc Datas
                elif (seconds % 60 == 0 and seconds != 0):
                    try:
                        obj = self.RustyPot_misc("chat")

                        ## Update Stats
                        if obj["userCount"] != 0:
                            totalUserCount += obj["userCount"]
                            averageUserCount["count"] = floor(totalUserCount / averageUserCount["iterations"])
                            averageUserCount["iterations"] += 1
                        chatMessages += len(obj["prevChatMessages"])
                        self.prevChatMessages = obj["prevChatMessages"]

                        # Flash Giveaway
                        if (obj.get("flashGiveawayPrice") and lastFgPrice != obj["flashGiveawayPrice"]):
                            lastFgPrice = obj["flashGiveawayPrice"]
                            flashGiveawayPayout += obj["flashGiveawayPrice"]
                            flashGiveaways += 1

                        ## Check disconnection
                        try:
                            lastMessage = self.get_innerText("#chatArea .chatMessage:last-child > span")
                            lastMessageOwner = self.get_innerText("#chatArea .chatMessage:last-child > b")
                            if ("Disconnected from server, Attempting to reconnect..." in lastMessage and "[Admin]" in lastMessageOwner):
                                driver.refresh()
                        except:
                            driver.refresh()
                    except:
                        print(traceback.format_exc())
                        sleep(1)
                        self.log(self.prefix + "Jackpot", False)

                # Save Datas to DB
                if (seconds == 0):
                    seconds = secondsOG

                    # Get DB Datas
                    stats = self.db.getOne("stats")

                    ## Update Jackpot Datas
                    lastJackpots_raw = self.db.getLastN("jackpots", max(ceil(secondsOG / 120), 10) + 1, "games")
                    lastJackpots = []

                    for j in lastJackpots_raw:
                        for k in j["games"]:
                            lastJackpots.append(k)

                    games = list(filter(lambda x: x["id"] not in lastJackpots, games))
                    playedGames = len(games)
                    gamesBlock = {}

                    # Get replaced IDs
                    ids = []

                    for game in games:
                        ids.append(game["id"])
                        totalWager += game["wager"]
                        if (game["wager"] > biggestGame): biggestGame = game["wager"]

                    date = datetime.datetime.now()
                    if (playedGames > 0):
                        gamesBlock = {
                            "wager": totalWager,
                            "games": ids,
                            "biggest": biggestGame,
                            "date": self.helpers.hour_rounder_ceil(date),
                        }

                    # Players
                    if (stats.get("players") == None): stats["players"] = []

                    # Merge Users
                    new_misc = list(users)
                    new_misc.extend(x for x in stats["players"] if x not in new_misc)
                    stats["players"] = new_misc

                    ## Update Misc Datas
                    miscBlock = {
                        "date": self.helpers.hour_rounder_ceil(date),
                        "flashGiveaways": flashGiveaways,
                        "flashGiveawayPayout": flashGiveawayPayout,
                        "chatMessages": len(self.prevChatMessages),
                        "averageUserCount": averageUserCount,
                        "playersCount": self.playersCount
                    }

                    # Update DB and log the date
                    self.db.update("stats", {}, stats)
                    self.db.insertOne("miscs", miscBlock)

                    if (playedGames > 0 and gamesBlock.get("games") != None):
                        self.db.insertOne("jackpots", gamesBlock)

                    print(date, ": (RustyPot) Jackpot, Misc - Saved to DB")

                    ## Reset local variables
                    # MISC
                    chatMessages = 0
                    totalUserCount = 0
                    averageUserCount = { "count": 0, "iterations": 1 }
                    flashGiveaways = 0
                    flashGiveawayPayout = 0

                    # JACKPOT
                    totalWager = 0
                    playedGames = 0
                    biggestGame = 0
                    games = []
                    ids = []

                    new_messages = list(self.savedMessages)
                    new_messages.extend(x for x in self.prevChatMessages if x not in new_messages)

                    self.savedMessages = new_messages.copy()
                    self.prevChatMessages = []
                    self.playersCount = 0

                    # Refetch stats
                    stats = self.db.getOne("stats")

                sleep(secMult)
        except:
            print(traceback.format_exc())
            self.log(self.prefix + "Jackpot", False)
            self.local_reset("jackpot")

    def RustyPot_misc(self, event):
        # Messages in Chat + Online User Count
        returnObj = {}

        if (event == "chat"):
            try:
                # Average User Count
                onlinePlayers = self.get_innerText(".panel-heading .Online_players")
                if not onlinePlayers: raise "No Online Users!"
                returnObj["userCount"] = int(onlinePlayers)

                # Store chat messages in an array
                prev = []
                messageElements = self.get_elements('.chatMessage > span')
                if not messageElements: raise "No messages"
                for messageEl in messageElements:
                    rawMessage = messageEl.get_attribute("innerText")

                    # Filter out flash giveaway announcements
                    if "A Flash Giveaway has started Good Luck to All!" not in rawMessage and "These giveaways are hosted randomly stay tuned for more!" not in rawMessage and rawMessage not in self.savedMessages:
                        prev.append(rawMessage)

                try:
                    # Find total chat messages
                    new = list(prev)
                    new.extend(x for x in self.prevChatMessages if x not in new)

                    returnObj["prevChatMessages"] = new
                except Exception as e:
                    print(traceback.format_exc())

                # Flash giveaways
                try:
                    flashGiveawayPrice = float(self.get_innerText("#fgPrice")[1:])
                    returnObj["flashGiveawayPrice"] = flashGiveawayPrice
                except Exception as e:
                    print(traceback.format_exc())

            except Exception as e:
                print(traceback.format_exc())
                returnObj["userCount"] = 0
                returnObj["prevChatMessages"] = []

        return returnObj