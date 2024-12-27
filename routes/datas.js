const express = require('express');
const moment = require('moment');
const Password = require('../funcs/password');

// Data
const RustyPot = require('./data/rustypot');
const RustMagic = require('./data/rustmagic');
const BanditCamp = require('./data/banditcamp');

const router = express.Router();
const P = new Password();

router.get("/:web/:id", P.verifyJwt, async (req, res) => {

    try {
        if (!req?.user) return res.send({ data: [] });

        let start = req.query.start,
            end = req.query.end;

        if (!start && !end) {
            start = moment("2023/10/25").toDate();
            end = new Date();
        } else {
            start = new Date(start);
            end = new Date(end);
        }

        if (moment(start).isSame(end)) end = new Date(end.getTime() + 1000 * 60 * 60 * 24);

        const dateQuery = {
            $and: [
                { date: { $gte: start } },
                { date: { $lte: end } }
            ]
        }

        // Mandatory Parameters
        let id = req.params.id;
        let web = req.params.web;

        if (!id || !web) return res.send({ data: [] });

        switch (web) {
            case "RustyPot":
                RustyPot({ id, dateQuery, start, end })
                    .then(data => res.send(data))
                    .catch(() => {});
                break

            case "BanditCamp":
                BanditCamp({ id, dateQuery, start, end })
                    .then(data => res.send(data))
                    .catch(() => {});
                break

            case "RustMagic":
                RustMagic({ id, dateQuery, start, end })
                    .then(data => res.send(data))
                    .catch(() => {});
                break
        }
    } catch (e) {
        console.log(e);
        return res.send({ data: [] });
    }
});

module.exports = router;