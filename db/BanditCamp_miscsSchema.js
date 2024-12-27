const mongoose = require("mongoose");
const Schema = mongoose.Schema;

const BanditCamp_miscsSchema = new Schema({
    rainAmount: Number,
    averageRainValue: Number,
    chatMessages: Number,
    uniquePlayersChat: Number,
    averageUserCount: Number,
    totalLeaderboardWager: Number,
    date: Date,
});

const BanditCamp_miscsModel = mongoose.model('banditcamp_miscs', BanditCamp_miscsSchema);
module.exports = BanditCamp_miscsModel;