const mongoose = require("mongoose");
const Schema = mongoose.Schema;

const RustyPot_coinflipSchema = new Schema({
    wager: Number,
    games: [String],
    bots: Number,
    jimmy: Number,
    cancelled: Number,
    date: Date,
});

const RustyPot_coinflipModel = mongoose.model('rustypot_coinflips', RustyPot_coinflipSchema);
module.exports = RustyPot_coinflipModel;