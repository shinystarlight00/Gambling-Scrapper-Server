const express = require('express');
const router = express.Router();

/* ROUTES */
const auth = require('./auth');
const stats = require('./stats');
const datas = require('./datas');
const script = require('./script');

router.use('/auth', auth);
router.use('/stats', stats);
router.use('/datas', datas);
router.use('/script', script);

module.exports = router;