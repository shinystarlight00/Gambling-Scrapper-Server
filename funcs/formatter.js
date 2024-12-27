/**
 * This class will be used once (hopefully)
 * The purpose is merging old database records to a new schema
 */

const RustyPotsCoinflipDB = require('../db/RustyPot_coinflipSchema');
const RustyPotsJackpotDB = require('../db/RustyPot_jackpotSchema');
const RustyPotsStatsDB = require('../db/RustyPot_statsSchema');
const RustyPotsMiscDB = require('../db/RustyPot_miscsSchema');

const { roundToHour } = require('./helpers');

// Formatters (One-time-only functions)
class Format {
    constructor() {
        this.formatCoinflip();
        this.formatJackpot();
        this.formatMisc();
    }

    formatCoinflip() {
        return new Promise(async (resolve, reject) => {
            // Get the games
            let coinflips = await RustyPotsCoinflipDB.find({}).sort({ date: 1 }).lean();
            let stats = await RustyPotsStatsDB.findOne({}).lean();

            // Update
            let arr = [],
                ids = [],
                prevDate = roundToHour(coinflips[0]["date"]),
                totalWager = 0,
                playedGames = 0,
                botGames = 0,
                jimmy = 0;

            for (let i = 0; i < coinflips.length; i++) {
                let game = coinflips[i];

                // Round the date of the game
                let localDate = roundToHour(game["date"]);

                // Update stats
                totalWager += game["wager"];
                playedGames++;
                ids.push(game["_id"]);
                if (game["jimmyWon"] == true || game["jimmyWon"] == false) botGames++;
                if (game["jimmyWon"] == true) jimmy++;

                // Next hour
                if (prevDate.getTime() != localDate.getTime()) {
                    // Add to the array first
                    arr.push({
                        "wager": totalWager,
                        "games": ids,
                        "jimmy": jimmy,
                        "bots": botGames,
                        "date": localDate
                    })

                    // Reset
                    totalWager = 0;
                    playedGames = 0;
                    botGames = 0;
                    jimmy = 0;
                    ids = [];
                }

                prevDate = localDate;
            }

            // Distribute cancelled games over time
            let cancelledGames = stats.cancelledCoinflipGames;
            for (let i = 0; i < arr.length; i++) {
                let percent = arr[i].games.length / coinflips.length;
                arr[i] = { ...arr[i], cancelled: Math.round(percent * cancelledGames) }
            }

            // Clear the DB and save the array into it
            await RustyPotsCoinflipDB.deleteMany({});
            await RustyPotsCoinflipDB.insertMany(arr);

            return resolve();
        })
    }

    formatJackpot() {
        return new Promise(async (resolve, reject) => {
            // Get the games
            let jackpots = await RustyPotsJackpotDB.find({}).sort({ date: 1 }).lean();

            // Update
            let arr = [],
                ids = [],
                prevDate = roundToHour(jackpots[0]["date"]),
                totalWager = 0,
                biggestGame = 0,
                playedGames = 0;

            for (let i = 0; i < jackpots.length; i++) {
                let game = jackpots[i];

                // Round the date of the game
                let localDate = roundToHour(game["date"]);

                // Update stats
                totalWager += game["wager"];
                ids.push(game["_id"]);
                playedGames++;

                if (prevDate.getTime() == localDate.getTime()) {
                    // Find the biggest game
                    if (game["wager"] > biggestGame) biggestGame = game["wager"];
                }

                // Next hour
                if (prevDate.getTime() != localDate.getTime() || i == jackpots.length - 1) {
                    if (game["wager"] > biggestGame) biggestGame = game["wager"];

                    // Add to the array first
                    arr.push({
                        "wager": totalWager,
                        "games": ids,
                        "biggest": biggestGame,
                        "date": localDate
                    })

                    // Reset
                    totalWager = 0;
                    biggestGame = 0;
                    playedGames = 0;
                    ids = [];
                }

                prevDate = localDate;
            }

            // Clear the DB and save the array into it
            await RustyPotsJackpotDB.deleteMany({});
            await RustyPotsJackpotDB.insertMany(arr);

            return resolve();
        })
    }

    formatMisc() {
        return new Promise(async (resolve, reject) => {
            let miscs = await RustyPotsMiscDB.findOne({}).lean();
            let stats = await RustyPotsStatsDB.findOne({}).lean();

            stats["players"] = [...miscs["players"]];
            miscs = [];

            // Distribute misc values in stats to miscs collection
            let flashGiveawayPayout = stats["flashGiveawayPayout"],
                averageUserCount = stats["averageUserCount"],
                flashGiveaways = stats["flashGiveaways"],
                chatMessages = stats["chatMessages"];

            let distribute = {
                chatMessages,
                flashGiveaways,
                // flashGiveawayPayout,
            }

            let result = [];
            let jackpots = await RustyPotsCoinflipDB.find({}).sort({ date: 1 }).lean(),
                firstDate = jackpots[0].date,
                lastDate = new Date();

            const h = 60 * 60 * 1000;
            let k = (lastDate - firstDate) / h + 1;

            // I don't know how to explain next steps,
            // a weird formula I found to distribute data close to perfect
            for (let [key, val] of Object.entries(distribute)) {
                let division = val / k,
                    rounded = Math.round(division),
                    difference = division - rounded,
                    roundedDifference = Math.round(difference * 10);

                // Find the first integer that makes roundedDifference greater than 100
                let multiplier = Math.ceil(100 / roundedDifference);
                let every = Math.round(multiplier / 10);
                distribute[key] = every;
            }

            for (let j = 0; j < k; j++) {
                result.push({
                    date: new Date(firstDate.getTime() + j * h),
                    averageUserCount: { count: averageUserCount.count, iterations: 60 },
                    flashGiveawayPayout: flashGiveawayPayout / k,
                    flashGiveaways: Math.round(flashGiveaways / k + (j % distribute["flashGiveaways"] == 0 ? 1 : 0)),
                    chatMessages: Math.round(chatMessages / k + (j % distribute["chatMessages"] == 0 ? 1 : 0)),
                    playersCount: Math.round(stats["players"].length / k),
                })
            }

            // Clear the DB and save the array into it
            await RustyPotsMiscDB.deleteMany({});
            await RustyPotsMiscDB.insertMany(result);
            await RustyPotsStatsDB.updateOne({}, stats);

            return resolve();
        })
    }
}

module.exports = Format;