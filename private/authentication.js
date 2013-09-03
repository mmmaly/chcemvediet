var passport = require("passport"),
    LocalStrategy = require('passport-local').Strategy;

exports.init = function(app) {

    passport.use(new LocalStrategy(
        function(username, password, done) {

            if (username == "chuck" && password == "norris")
                return done(null, { username: "chuck", language: "en" });

            if (username == "robert" && password == "fico")
                return done(null, { username: "robert", language: "sk" });

            return done(null, false, { message: "Login failed." });
        }
    ));

    passport.serializeUser(function(user, done) {
        done(null, JSON.stringify(user));
    });

    passport.deserializeUser(function(user, done) {
        done(null, JSON.parse(user));
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
    })
};