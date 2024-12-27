const mongoose = require("mongoose");
const Schema = mongoose.Schema;

const RustyPot_miscsSchema = new Schema({
    averageUserCount: Object,
    flashGiveawayPayout: Number,
    flashGiveaways: Number,
    chatMessages: Number,
    playersCount: Number,
    date: Date,
});

const RustyPot_miscsModel = mongoose.model('rustypot_miscs', RustyPot_miscsSchema);
module.exports = RustyPot_miscsModel;