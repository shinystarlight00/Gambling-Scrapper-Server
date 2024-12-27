const express = require('express');
const moment = require('moment');
const Password = require('../funcs/password');
const { ignoreDates } = require('../funcs/result_filter');

const router = express.Router();
const P = new Password();

/* Scrape DBs */
// RustyPot
const RustyPotsCoinflipDB = require('../db/RustyPot_coinflipSchema');
const RustyPotsJackpotDB = require('../db/RustyPot_jackpotSchema');
const RustyPotsMiscDB = require('../db/RustyPot_miscsSchema');

// BanditCamp
const BanditCampSpinnerDB = require('../db/BanditCamp_spinnersSchema');
const BanditCampCrateDB = require('../db/BanditCamp_cratesSchema');
const BanditCampWheelDB = require('../db/BanditCamp_wheelsSchema');
const BanditCampMiscsDB = require('../db/BanditCamp_miscsSchema');

// RustClash


// Howl


//RustMagic
const RustMagicLiveDB = require('../db/RustMagic_livesSchema');


/* RustyPot */
router.get("/RustyPot", P.verifyJwt, async (req, res) => {

    function coinflipPercentages(coinflips, botCoinflipGames) {
        try {
            // Get coinflip stats
            let games = 0,
                jimmyWon = 0;

            coinflips.forEach(c => {
                games += c?.games?.length || 0;
                jimmyWon += c?.jimmy || 0;
            });

            // Coinflip Percentage Calculations
            let coinflipPlayerVsPlayerGames = (games - botCoinflipGames) || 0;
            let coinflipBotVsPlayerGames = botCoinflipGames || 0;

            let coinflipJimmyWinPercentage = (jimmyWon / coinflipBotVsPlayerGames * 100) || 0;
            let coinflipPlayerVsPlayerPercentage = (coinflipPlayerVsPlayerGames / games) * 100
            let coinflipBotVsPlayerPercentage = (coinflipBotVsPlayerGames / games) * 100

            return {
                coinflipJimmyWinPercentage,
                coinflipPlayerVsPlayerPercentage,
                coinflipBotVsPlayerPercentage
            }
        } catch (e) {
            console.log(e);
            return {
                coinflipJimmyWinPercentage: 0,
                coinflipPlayerVsPlayerPercentage: 0,
                coinflipBotVsPlayerPercentage: 0,
            }
        }
    }

    try {
        if (!req?.user) return res.send({ stats: {} });

        let start = req?.query?.start,
            end = req?.query?.end;

        if (!start && !end) {
            start = moment("2023/10/25").toDate();
            end = new Date();
        } else {
            start = new Date(start);
            end = new Date(end);
        }

        if (moment(start).isSame(end)) end = new Date(end.getTime() + 1000 * 60 * 60 * 24);

        const dateQuery = {
            $and: [
                { date: { $gte: start } },
                { date: { $lte: end } }
            ]
        }

        let coinflips = await RustyPotsCoinflipDB.find(dateQuery).lean();
        let jackpots = await RustyPotsJackpotDB.find(dateQuery).lean();
        let miscs = await RustyPotsMiscDB.find(dateQuery).lean();

        let arr = ignoreDates([coinflips, jackpots, miscs], "rustypot");
        [coinflips, jackpots, miscs] = [...arr];

        // Return stats
        let jackpotGames = 0,
            totalJackpotWager = 0,
            biggestJackpotGame = 0;

        let coinflipGames = 0,
            botCoinflipGames = 0,
            totalCoinflipWager = 0,
            cancelledCoinflipGames = 0;

        let chatMessages = 0,
            uniquePlayers = 0,
            flashGiveaways = 0,
            userCountTotal = 0,
            flashGiveawayPayout = 0,
            userCountIterations = 0;

        for (let j of jackpots) {
            jackpotGames += j["games"]?.length || 0;
            totalJackpotWager += j["wager"] || 0;
            if (j["biggest"] > biggestJackpotGame) biggestJackpotGame = j["biggest"];
        }

        for (let c of coinflips) {
            coinflipGames += c["games"]?.length || 0;
            totalCoinflipWager += c["wager"] || 0;
            botCoinflipGames += c["bots"] || 0;
            cancelledCoinflipGames += c["cancelled"] || 0;
        }

        for (let m of miscs) {
            uniquePlayers += m["playersCount"] || 0;
            chatMessages += m["chatMessages"] || 0;
            flashGiveaways += m["flashGiveaways"] || 0;
            flashGiveawayPayout += m["flashGiveawayPayout"] || 0;
            userCountTotal += m?.["averageUserCount"]?.["count"] || 0;
            userCountIterations += m?.["averageUserCount"]?.["iterations"] || 0;
        }

        estimatedProfit = (totalJackpotWager + totalCoinflipWager) * 5 / 100;

        const stats_raw = {
            // Jackpot
            averageJackpotWager: totalJackpotWager / jackpotGames,
            playedJackpotGames: jackpotGames,
            totalJackpotWager,
            biggestJackpotGame,

            // Coinflip
            averageCoinflipWager: totalCoinflipWager / coinflipGames,
            playedCoinflipGames: coinflipGames,
            totalCoinflipWager,
            estimatedProfit,
            botCoinflipGames,
            cancelledCoinflipGames,
            ...coinflipPercentages(coinflips, botCoinflipGames),

            // Misc
            uniquePlayers,
            chatMessages,
            flashGiveaways,
            flashGiveawayPayout,
            averageUserCount: { count: Math.round(userCountTotal / miscs.length), iterations: Math.round(userCountIterations / miscs.length) },
        }

        delete stats_raw["players"];

        return res.send({ stats: stats_raw });
    } catch (e) {
        console.log(e);
        return res.send({ stats: {} });
    }
});

/* BanditCamp */
router.get("/BanditCamp", P.verifyJwt, async (req, res) => {
    try {
        if (!req?.user) return res.send({ stats: {} });

        let start = req?.query?.start,
            end = req?.query?.end;

        if (!start && !end) {
            start = moment("2023/10/25").toDate();
            end = new Date();
        } else {
            start = new Date(start);
            end = new Date(end);
        }

        if (moment(start).isSame(end)) end = new Date(end.getTime() + 1000 * 60 * 60 * 24);

        const dateQuery = {
            $and: [
                { date: { $gte: start } },
                { date: { $lte: end } }
            ]
        }

        let miscs = await BanditCampMiscsDB.find(dateQuery).lean();
        let crates = await BanditCampCrateDB.find(dateQuery).lean();
        let wheels = await BanditCampWheelDB.find(dateQuery).lean();
        let spinners = await BanditCampSpinnerDB.find(dateQuery).lean();

        let arr = ignoreDates([miscs, crates, wheels, spinners], "banditcamp");
        [miscs, crates, wheels, spinners] = [...arr];

        // Return stats
        let playedCratesGames = 0,
            botCrateGames = 0,
            totalCratesWager = 0,
            averageCratesWager = 0,
            uniqueCratesPlayers = 0;

        let playedWheelGames = 0,
            botWheelGames = 0,
            totalWheelWager = 0,
            totalWheelPlayers = 0,
            averageWheelWager = 0,
            averageWheelPlayers = 0;

        let playedSpinnerGames = 0,
            totalSpinnerWager = 0,
            averageSpinnerWager = 0;

        let rainAmount = 0,
            chatMessages = 0,
            averageRainValue = 0,
            averageUserCount = 0,
            uniquePlayersChat = 0,
            totalLeaderboardWager = 0,
            averageLeaderboardWager = 0;

        for (let c of crates) {
            playedCratesGames += (c["games"] + c["bots"]) || 0;
            botCrateGames += c["bots"] || 0;
            totalCratesWager += c["wager"] || 0;
            uniqueCratesPlayers += c["uniquePlayers"] || 0;
        }

        averageCratesWager = totalCratesWager / Math.max(1, (playedCratesGames - botCrateGames));

        for (let w of wheels) {
            playedWheelGames += w["games"]|| 0;
            totalWheelWager += w["wager"] || 0;
            totalWheelPlayers += w["players"] || 0;
        }

        averageWheelWager = totalWheelWager / Math.max(1, playedWheelGames);
        averageWheelPlayers = totalWheelPlayers / Math.max(1, playedWheelGames);

        for (let s of spinners) {
            playedSpinnerGames += s["games"] || 0;
            totalSpinnerWager += s["wager"] || 0;
        }

        averageSpinnerWager = totalSpinnerWager / Math.max(1, playedSpinnerGames);

        for (let m of miscs) {
            rainAmount += m["rainAmount"] || 0;
            chatMessages += m["chatMessages"] || 0;
            averageUserCount += m["averageUserCount"] || 0;
            uniquePlayersChat += m["uniquePlayersChat"] || 0;
            totalLeaderboardWager += m["totalLeaderboardWager"] || 0;
            averageRainValue += (m["averageRainValue"] * m["rainAmount"]) || 0;
        }

        totalLeaderboardWager = totalLeaderboardWager / (miscs.filter(m => m["totalLeaderboardWager"]).length);
        averageUserCount = averageUserCount / (miscs.filter(m => m["averageUserCount"]).length);
        averageLeaderboardWager = totalLeaderboardWager / 10;
        averageRainValue = averageRainValue / rainAmount;

        const stats_raw = {
            // Crates
            playedCratesGames,
            averageCratesWager,
            uniqueCratesPlayers,
            totalCratesWager,

            // Wheel
            totalWheelWager,
            playedWheelGames,
            totalWheelPlayers,
            averageWheelWager,
            averageWheelPlayers,

            // Spinner
            playedSpinnerGames,
            averageSpinnerWager,
            totalSpinnerWager,

            // Misc
            rainAmount,
            averageRainValue,
            chatMessages,
            uniquePlayersChat,
            averageUserCount,
            totalLeaderboardWager,
            averageLeaderboardWager,
        }

        return res.send({ stats: stats_raw });
    } catch (e) {
        console.log(e);
        return res.send({ stats: {} });
    }
});

/* RustClash */
router.get("/RustClash", async (req, res) => {
    return res.send({ stats: {} });
});

/* Howl */
router.get("/Howl", async (req, res) => {
    return res.send({ stats: {} });
});

/* RustMagic */
router.get("/RustMagic", P.verifyJwt, async (req, res) => {
    try {
        if (!req?.user) return res.send({ stats: {} });

        let start = req?.query?.start,
            end = req?.query?.end;

        if (!start && !end) {
            start = moment("2023/10/25").toDate();
            end = new Date();
        } else {
            start = new Date(start);
            end = new Date(end);
        }

        if (moment(start).isSame(end)) end = new Date(end.getTime() + 1000 * 60 * 60 * 24);

        const dateQuery = {
            $and: [
                { date: { $gte: start } },
                { date: { $lte: end } }
            ]
        }

        let live = await RustMagicLiveDB.find(dateQuery).lean();

        let arr = ignoreDates([live], "rustmagic");
        [live] = [...arr];

        // Return stats
        const stats_raw = {
            "Total Data": {
                "games": 0,
                "wager": 0,
                "payout": 0,
            }
        };

        for (let game of live) {
            let gameName = game["game"];
            if (!stats_raw?.[gameName]) stats_raw[gameName] = {
                "games": 0,
                "wager": 0,
                "payout": 0,
            };

            let local_games = game["games"],
                local_wager = game["wager"],
                local_payout = game["payout"];

            // Game Data
            stats_raw[gameName]["games"] += local_games;
            stats_raw[gameName]["wager"] += local_wager;
            stats_raw[gameName]["payout"] += local_payout;

            // Total Data
            stats_raw["Total Data"]["games"] += local_games;
            stats_raw["Total Data"]["wager"] += local_wager;
            stats_raw["Total Data"]["payout"] += local_payout;
        }

        return res.send({ stats: stats_raw });
    } catch (e) {
        console.log(e);
        return res.send({ stats: {} });
    }
});

module.exports = router;