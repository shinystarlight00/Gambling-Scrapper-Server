const moment = require('moment');

function calculateInterval(desired, start, end) {
    let result = [];
    let gamesAndDates = {};

    // Calculate the interval within the given data from client-side
    let interval, intervalType = "day";
    interval = Math.max(moment(end).diff(start, 'days'), 1);

    if (interval <= 2) intervalType = "hour";
    else if (interval >= 210) intervalType = "month";
    else if (interval >= 49) intervalType = "week";

    interval = moment(end).diff(start, intervalType + "s");

    // Round game dates
    for (let game of desired) {
        let date = moment(game["date"]).startOf(intervalType);

        // Create an date-game object
        delete game["_id"];
        delete game["date"];
        if (!gamesAndDates?.[date]) gamesAndDates[date] = [game];
        else gamesAndDates[date].push(game);
    }

    // Fill the empty dates with 0 value
    let intervalTypeAsMiliseconds;
    switch(intervalType) {
        case "hour":
            intervalTypeAsMiliseconds = 60 * 60 * 1000;
            break;
        case "day":
            intervalTypeAsMiliseconds = 60 * 60 * 1000 * 24;
            break;
        case "week":
            intervalTypeAsMiliseconds = 60 * 60 * 1000 * 24 * 7;
            break;
        case "month":
            intervalTypeAsMiliseconds = 60 * 60 * 1000 * 24 * 30;
            break;
    }

    for (let i = 0; i < Math.ceil((end.getTime() - start.getTime()) / intervalTypeAsMiliseconds); i++) {
        let localDate = new Date(start.getTime() + i * intervalTypeAsMiliseconds);

        result.push({
            date: localDate,
            value: 0
        });
    }

    return { result, gamesAndDates, intervalType };
}

module.exports = calculateInterval