const express = require("express");
const jwt = require("jsonwebtoken");
const userDB = require("../db/userSchema");
const Password = require("../funcs/password");
const router = express.Router();

const P = new Password();

router.post("/login", async (req, res) => {
  try {
    const { username, password } = req.body;

    if (!username || !password)
      return res.status(400).send({
        success: 0,
        message: "User cannot be found",
      });

    let user = await userDB.find({ username });

    if (user?.length == 0)
      return res.status(400).send({
        success: 0,
        message: "User cannot be found",
      });

    user = user[0];

    // Compare password
    P.checkPasswords(user.password, password)
      .then(() => {
        try {
          const token = jwt.sign({ id: user._id }, process.env.JWT_SECRET);
          return res.send({ success: true, token });
        } catch (e) {
          console.log(e);
          return res
            .status(400)
            .send({ success: 0, message: "An error occured" });
        }
      })
      .catch((e) => {
        console.log(e);
        return res.status(400).send({ success: 0, message: e });
      });
  } catch (e) {
    console.log(e);
    return res.status(400).send({ success: 0, message: "An error occured" });
  }
});

router.post("/check-login", P.verifyJwt, async (req, res) => {
  try {
    if (req?.user)
      return res.send({
        user: { username: req.user.email },
        success: true,
      });
    return res.send({ user: null, success: false });
  } catch (e) {
    console.log(e);
    return res.send({ user: null, success: false });
  }
});

module.exports = router;
