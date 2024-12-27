require('dotenv');
const express = require('express');
const { exec } = require('child_process');
const Password = require('../funcs/password');
const router = express.Router();

const P = new Password();

router.get("/restart", P.verifyJwt, async (req, res) => {
    try {
        if (!req?.user) return res.send({ status: false });

        // Kills Python & Chrome process and restarts
        exec(process.env.RESET_COMMAND, (err, stdout, stderr) => {
            if (err) {
                console.log(err);
                return res.send({ status: false });
            }
            else return res.send({ status: true });
        });
    } catch(e) {
        console.log(e);
        return res.send({ status: false });
    }
});

module.exports = router;