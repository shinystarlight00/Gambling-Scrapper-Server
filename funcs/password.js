const bcrypt = require("bcrypt");
const jwt = require('jsonwebtoken');
const userDB = require('../db/userSchema');

module.exports = class Password {
    createPassword(p) {
        return new Promise((resolve, reject) => {
            bcrypt
            .genSalt(10)
            .then(salt => {
                return bcrypt.hash(p, salt)
            })
            .then(hash => {
                return resolve(hash);
            })
            .catch(e => {
                console.log(e);
                reject(e);
            });
        })
    }

    checkPasswords(hash, p) {
        return new Promise((resolve, reject) => {
            try {
                bcrypt
                .compare(p, hash)
                .then(res => {
                    if (res) return resolve();
                    return reject("Wrong Password");
                });
            } catch(e) {
                console.log(e);
                return reject(e);
            }
        });
    }

    // Middleware
    verifyJwt(req, res, next) {
        try {
            const token = req?.headers?.["access-token"];
            req.user = null;

            if (token) {
                jwt.verify(token, process.env.JWT_SECRET, async (err, decoded) => {
                    if (!err) {
                        let id = decoded.id;

                        // Check user login
                        let user = await userDB.find({ _id: id });
                        if (user?.length > 0) req.user = user[0];

                        next();
                    } else console.log(err);
                });
            } else next();
        } catch (e) {
            next();
        }
    }

    // Password verification but it's not a middleware
    verifyJwtFunc(token) {
        return new Promise(async (resolve, reject) => {
            if (!token) return resolve(null);

            jwt.verify(token, process.env.JWT_SECRET, async (err, decoded) => {
                if (err) {
                    console.log(err);
                    return resolve(null);
                }
    
                let id = decoded.id;
    
                // Check user login
                let user = await userDB.find({ _id: id });
                if (user?.length > 0) return resolve(user[0]);
                return resolve(null);
            });
        })
    }
}