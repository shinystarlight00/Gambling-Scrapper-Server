const mongoose = require("mongoose");
const Schema = mongoose.Schema;

const BanditCamp_statsSchema = new Schema({
    players: [String]
});

const BanditCamp_statsModel = mongoose.model('banditcamp_stats', BanditCamp_statsSchema);
module.exports = BanditCamp_statsModel;