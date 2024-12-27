const mongoose = require("mongoose");
const Schema = mongoose.Schema;

const userSchema = new Schema({
    username: String,
    password: String, // Hash
});

const UserModel = mongoose.model('users', userSchema);
module.exports = UserModel;