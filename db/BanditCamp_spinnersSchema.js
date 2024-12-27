const mongoose = require("mongoose");
const Schema = mongoose.Schema;

const BanditCamp_spinnersSchema = new Schema({
  games: Number,
  wager: Number,
  date: Date,
});

const BanditCamp_spinnersModel = mongoose.model(
  "banditcamp_spinners",
  BanditCamp_spinnersSchema
);
module.exports = BanditCamp_spinnersModel;
