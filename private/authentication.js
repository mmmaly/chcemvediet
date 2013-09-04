var db = require("./db"),
    crypto = require("crypto"),
    User = require("./models/user").User,
    passport = require("passport"),
    LocalStrategy = require('passport-local').Strategy;

exports.init = function(app) {

    passport.use(new LocalStrategy(
        function(email, password, done) {

            var passwordHash = crypto.createHash('md5').update(password).digest("hex");

            db.getUser(email)
                .then(function (user) {
                    if (user && user.password === passwordHash)
                        done(null, new User(user));
                    else
                        done(null, false);
                },
                done.bind(null, null, false));
        }
    ));

    passport.serializeUser(function(user, done) {
        done(null, JSON.stringify(user));
    });

    passport.deserializeUser(function(user, done) {
        done(null, new User(JSON.parse(user)));
    });

    app.post("/login", function (req, res) {
        var authMethod = req.body.authMethod || "local";
        passport.authenticate(authMethod, function (err, user) {

            if (err)
                return res.json({ error: res.__("Login error") });
            else if (!user)
                return res.json({ error: res.__("Login failed") });

            req.login(user, function(err) {
                if (err)
                    return res.json({ error: res.__("Login error") });

                return res.json({ success: true });
            });

        })(req, res);
    });

    app.post("/logout", function(req, res) {
        req.logout();
        res.end();
    });
};