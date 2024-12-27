const mongoose = require("mongoose");
const Schema = mongoose.Schema;

const BanditCamp_wheelsSchema = new Schema({
    players: Number,
    games: Number,
    wager: Number,
    date: Date,
});

const BanditCamp_wheelsModel = mongoose.model('banditcamp_wheels', BanditCamp_wheelsSchema);
module.exports = BanditCamp_wheelsModel;