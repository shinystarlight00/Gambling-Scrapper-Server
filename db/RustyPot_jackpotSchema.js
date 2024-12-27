const mongoose = require("mongoose");
const Schema = mongoose.Schema;

const RustyPot_jackpotSchema = new Schema({
    wager: Number,
    games: [String],
    biggest: Number,
    date: Date
});

const RustyPot_jackpotModel = mongoose.model('rustypot_jackpots', RustyPot_jackpotSchema);
module.exports = RustyPot_jackpotModel;