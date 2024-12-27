const calculateInterval = require('../../funcs/data_interval');
const { resultFilter } = require('../../funcs/result_filter');

// Database
const RustyPotsCoinflipDB = require('../../db/RustyPot_coinflipSchema');
const RustyPotsJackpotDB = require('../../db/RustyPot_jackpotSchema');
const RustyPotsMiscDB = require('../../db/RustyPot_miscsSchema');

function RustyPot({
    id,
    end,
    start,
    dateQuery,
}) {
    return new Promise(async (resolve, reject) => {
        try {
            // Get the corresponding datas from database
            let desired = [];
    
            if (id.toLowerCase().includes("coinflip")) {
                desired = await RustyPotsCoinflipDB.find(dateQuery).sort({ date: 1 }).lean();
            } else if (id.toLowerCase().includes("jackpot")) {
                desired = await RustyPotsJackpotDB.find(dateQuery).sort({ date: 1 }).lean();
            } else if (["estimatedProfit"].includes(id)) {
                desired = [
                    ...(await RustyPotsJackpotDB.find(dateQuery, { wager: 1, date: 1 }).sort({ date: 1 }).lean()),
                    ...(await RustyPotsCoinflipDB.find(dateQuery, { wager: 1, date: 1 }).sort({ date: 1 }).lean()),
                ]
            } else {
                desired = await RustyPotsMiscDB.find(dateQuery).sort({ date: 1 }).lean();
            }
    
            let intervalCalculation = calculateInterval(desired, start, end);
            let { result, gamesAndDates, intervalType } = intervalCalculation;
    
            // Percentage Calculations for Graph
            if (id.toLowerCase().includes("percentage")) {
                // Find the Bot Games
                let jimmyWonPercentage, playerGamesPercentage, botGamesPercentage;
                for (let [key, val] of Object.entries(gamesAndDates)) {
                    let botGamesCount = Object.values(val).reduce((a, b) => a + (b?.bots || 0), 0);;
    
                    botGamesPercentage = botGamesCount / Object.values(val).reduce((a, b) => a + (b?.games?.length || 0), 0) * 100;
                    playerGamesPercentage = 100 - botGamesPercentage;
                    jimmyWonPercentage = Object.values(val).reduce((a, b) => a + (b?.jimmy || 0), 0) / botGamesCount * 100;
    
                    if (id == "coinflipJimmyWinPercentage") result.push({
                        date: key,
                        value: jimmyWonPercentage
                    });
                    else if (id == "coinflipBotVsPlayerPercentage") result.push({
                        date: key,
                        value: botGamesPercentage
                    });
                    else if (id == "coinflipPlayerVsPlayerPercentage") result.push({
                        date: key,
                        value: playerGamesPercentage
                    });
                }
            } else {
                switch (id) {
                    case "playedJackpotGames":
                    case "playedCoinflipGames":
                        for (let [key, val] of Object.entries(gamesAndDates)) result.push({
                            date: key,
                            value: Object.values(val).reduce((a, b) => a + (b?.games?.length || 0), 0)
                        });
                        break;
    
                    case "averageJackpotWager":
                    case "averageCoinflipWager":
                        for (let [key, val] of Object.entries(gamesAndDates)) {
                            result.push({
                                date: key,
                                value: Object.values(val).reduce((a, b) => a + b.wager, 0) / Object.values(val).reduce((a, b) => a + (b?.games?.length || 0), 0)
                            });
                        }
                        break;
    
                    case "totalJackpotWager":
                    case "totalCoinflipWager":
                        for (let [key, val] of Object.entries(gamesAndDates)) {
                            result.push({
                                date: key,
                                value: Object.values(val).reduce((a, b) => a + b.wager, 0)
                            });
                        }
                        break;
    
                    case "estimatedProfit":
                        for (let [key, val] of Object.entries(gamesAndDates)) {
                            result.push({
                                date: key,
                                value: Object.values(val).reduce((a, b) => a + b.wager, 0) * ((req?.body?.estimatedPercent || 5) / 100)
                            });
                        }
                        break;
    
                    case "cancelledCoinflipGames":
                        for (let [key, val] of Object.entries(gamesAndDates)) result.push({
                            date: key,
                            value: Object.values(val).reduce((a, b) => a + (b?.cancelled || 0), 0)
                        });
                        break;
    
                    case "biggestJackpotGame":
                        for (let [key, val] of Object.entries(gamesAndDates)) {
                            let max = val.reduce((prev, current) => (prev && prev.biggest > current.biggest) ? prev : current).biggest;
                            result.push({
                                date: key,
                                value: max
                            });
                        }
                        break;
    
                    case "chatMessages":
                        for (let [key, val] of Object.entries(gamesAndDates)) {
                            result.push({
                                date: key,
                                value: Object.values(val).reduce((a, b) => a + b.chatMessages, 0)
                            });
                        }
                        break;
    
                    case "uniquePlayers":
                        for (let [key, val] of Object.entries(gamesAndDates)) {
                            result.push({
                                date: key,
                                value: Object.values(val).reduce((a, b) => a + b.playersCount, 0)
                            });
                        }
                        break;
    
                    case "averageUserCount":
                        for (let [key, val] of Object.entries(gamesAndDates)) {
                            result.push({
                                date: key,
                                value: Math.round(Object.values(val).reduce((a, b) => a + (b.averageUserCount.count * b.averageUserCount.iterations), 0) / Object.values(val).reduce((a, b) => a + b.averageUserCount.iterations, 0))
                            });
                        }
                        break;
    
                    case "flashGiveaways":
                        for (let [key, val] of Object.entries(gamesAndDates)) {
                            result.push({
                                date: key,
                                value: Object.values(val).reduce((a, b) => a + b.flashGiveaways, 0)
                            });
                        }
                        break;
    
                    case "flashGiveawayPayout":
                        for (let [key, val] of Object.entries(gamesAndDates)) {
                            result.push({
                                date: key,
                                value: Object.values(val).reduce((a, b) => a + b.flashGiveawayPayout, 0)
                            });
                        }
                        break;
                }
            }
    
            result = resultFilter(result, "rustypot");
    
            // Send
            return resolve({ data: result, intervalType });
        } catch(e) {
            console.error(e);
            return reject();
        }
    })
}

module.exports = RustyPot;