const mongoose = require("mongoose");
const Schema = mongoose.Schema;

const BanditCamp_cratesSchema = new Schema({
  uniquePlayers: Number,
  wager: Number,
  games: Number,
  bots: Number,
  date: Date,
});

const BanditCamp_cratesModel = mongoose.model(
  "banditcamp_crates",
  BanditCamp_cratesSchema
);
module.exports = BanditCamp_cratesModel;
