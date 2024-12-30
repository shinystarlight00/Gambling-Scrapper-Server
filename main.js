require('dotenv').config();
const mongoose = require("mongoose");
const express = require("express");
const bodyParser = require('body-parser');
const cors = require('cors');
const routes = require('./routes');

mongoose.connect(process.env.MONGO_URI);

const app = express();
const server = require('http').createServer(app);

/* Middlewares */
app.use(cors({ origin: process.env.CLIENT }));
app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());
app.use('/api', routes);

server.listen(process.env.PORT, '0.0.0.0');