const calculateInterval = require('../../funcs/data_interval');
const { resultFilter } = require('../../funcs/result_filter');

// Database
const BanditCampSpinnersDB = require('../../db/BanditCamp_spinnersSchema');
const BanditCampCratesDB = require('../../db/BanditCamp_cratesSchema');
const BanditCampWheelsDB = require('../../db/BanditCamp_wheelsSchema');
const BanditCampMiscsDB = require('../../db/BanditCamp_miscsSchema');

function BanditCamp({
    id,
    end,
    start,
    dateQuery,
}) {
    return new Promise(async (resolve, reject) => {
        try {
            // Get the corresponding datas from database
            let desired = [];

            if (id.toLowerCase().includes("spinner"))
                desired = await BanditCampSpinnersDB.find(dateQuery).sort({ date: 1 }).lean();
            else if (id.toLowerCase().includes("crate"))
                desired = await BanditCampCratesDB.find(dateQuery).sort({ date: 1 }).lean();
            else if (id.toLowerCase().includes("wheel"))
                desired = await BanditCampWheelsDB.find(dateQuery).sort({ date: 1 }).lean();
            else
                desired = await BanditCampMiscsDB.find(dateQuery).sort({ date: 1 }).lean();

            let intervalCalculation = calculateInterval(desired, start, end)
            let { result, gamesAndDates, intervalType } = intervalCalculation;

            switch (id) {
                case "playedSpinnerGames":
                case "playedCratesGames":
                case "playedWheelGames":
                    for (let [key, val] of Object.entries(gamesAndDates)) result.push({
                        date: key,
                        value: Object.values(val).reduce((a, b) => a + (b.games + (b?.bots || 0)), 0)
                    });
                    break;

                case "averageSpinnerWager":
                case "averageCratesWager":
                case "averageWheelWager":
                    for (let [key, val] of Object.entries(gamesAndDates)) {
                        result.push({
                            date: key,
                            value: Object.values(val).reduce((a, b) => a + b.wager, 0) / Object.values(val).reduce((a, b) => a + b.games, 0)
                        });
                    }
                    break;

                case "totalSpinnerWager":
                case "totalCratesWager":
                case "totalWheelWager":
                    for (let [key, val] of Object.entries(gamesAndDates)) {
                        result.push({
                            date: key,
                            value: Object.values(val).reduce((a, b) => a + b.wager, 0)
                        });
                    }
                    break;

                case "uniqueCratesPlayers":
                    for (let [key, val] of Object.entries(gamesAndDates)) {
                        result.push({
                            date: key,
                            value: Object.values(val).reduce((a, b) => a + b.uniquePlayers, 0)
                        });
                    }
                    break;

                case "averageWheelPlayers":
                    for (let [key, val] of Object.entries(gamesAndDates)) {
                        result.push({
                            date: key,
                            value: Object.values(val).reduce((a, b) => a + b.players, 0) / Object.values(val).reduce((a, b) => a + b.games, 0)
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

                case "uniquePlayersChat":
                    for (let [key, val] of Object.entries(gamesAndDates)) {
                        result.push({
                            date: key,
                            value: Math.round(Object.values(val).reduce((a, b) => a + b.uniquePlayersChat, 0))
                        });
                    }
                    break;

                case "averageUserCount":
                    for (let [key, val] of Object.entries(gamesAndDates)) {
                        let len = val.length;
                        result.push({
                            date: key,
                            value: Object.values(val).reduce((a, b) => a + b.averageUserCount, 0) / len
                        });
                    }
                    break;

                case "rainAmount":
                    for (let [key, val] of Object.entries(gamesAndDates)) {
                        result.push({
                            date: key,
                            value: Object.values(val).reduce((a, b) => a + b.rainAmount, 0)
                        });
                    }
                    break;

                case "averageRainValue":
                    for (let [key, val] of Object.entries(gamesAndDates)) {
                        let len = val.length;
                        result.push({
                            date: key,
                            value: Object.values(val).reduce((a, b) => a + b.averageRainValue, 0) / len
                        });
                    }
                    break;

                case "totalLeaderboardWager":
                case "averageLeaderboardWager":
                    for (let [key, val] of Object.entries(gamesAndDates)) {
                        let len = val.length;
                        console.log(gamesAndDates);
                        result.push({
                            date: key,
                            value: Object.values(val).reduce((a, b) => a + b.totalLeaderboardWager, 0) / (len * (id == "averageLeaderboardWager" ? 10 : 1))
                        });
                    }
                    break;
            }

            result = resultFilter(result, "banditcamp");
    
            // Send
            return resolve({ data: result, intervalType });
        } catch(e) {
            console.error(e);
            return reject();
        }
    })
}

module.exports = BanditCamp;