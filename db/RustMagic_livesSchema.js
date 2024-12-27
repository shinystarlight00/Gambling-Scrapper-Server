const mongoose = require("mongoose");
const Schema = mongoose.Schema;

const RustMagic_livesSchema = new Schema({
    payout: Number,
    wager: Number,
    games: Number,
    game: String,
    date: Date,
});

const RustMagic_livesModel = mongoose.model('rustmagic_lives', RustMagic_livesSchema);
module.exports = RustMagic_livesModel;