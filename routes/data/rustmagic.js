const calculateInterval = require('../../funcs/data_interval');
const { resultFilter } = require('../../funcs/result_filter');

// Database
const RustMagicLiveDB = require('../../db/RustMagic_livesSchema');

function RustMagic({
    id,
    end,
    start,
    dateQuery,
}) {
    return new Promise(async (resolve, reject) => {
        try {
            let index = "", game = "";

            if (id.endsWith("Wager")) index = "Wager";
            else if (id.endsWith("Games")) index = "Games";
            else if (id.endsWith("Payout")) index = "Payout";

            game = id.replace(index, "");

            if (game === "Total Data") filter = { ...dateQuery }
            else filter = {
                ...dateQuery,
                game
            }

            // Get the corresponding datas from database
            let desired = await RustMagicLiveDB
                .find(filter)
                .sort({ date: 1 })
                .lean();

            let intervalCalculation = calculateInterval(desired, start, end);
            let { result, gamesAndDates, intervalType } = intervalCalculation;

            switch(index) {
                case "Wager":
                    for (let [key, val] of Object.entries(gamesAndDates)) {
                        result.push({
                            date: key,
                            value: Object.values(val).reduce((a, b) => a + b.wager, 0)
                        });
                    }
                    break;

                case "Games":
                    for (let [key, val] of Object.entries(gamesAndDates)) {
                        result.push({
                            date: key,
                            value: Object.values(val).reduce((a, b) => a + b.games, 0)
                        });
                    }
                    break;

                case "Payout":
                    for (let [key, val] of Object.entries(gamesAndDates)) {
                        result.push({
                            date: key,
                            value: Object.values(val).reduce((a, b) => a + b.payout, 0)
                        });
                    }
                    break;
            }

            result = resultFilter(result, "rustmagic");

            // Send
            return resolve({ data: result, intervalType });
        } catch(e) {
            console.error(e);
            return reject();
        }
    })
}

module.exports = RustMagic;