var _ = require("underscore"),
    db = require("../db");

var languages = {
    "en": {
        code: "en",
        name: "English",
        icon: "/img/flag-us.png"
    },
    "sk": {
        code: "sk",
        name: "Slovensky",
        icon: "/img/flag-sk.png"
    }
};

_.extend(exports, {
    languages: languages,
    locales: _.keys(languages),
    process: function(req, res, next){
        // general handler for request language setting, to be registered with the express app

        var language = languages["sk"];
        if (req.user)
            language = req.user.language;
        else if (req.session && req.session.language)
            language = req.session.language;

        res.setLocale(language.code);

        // for use in the jade templates
        res.locals.user = req.user;
        res.locals.language = language;
        res.locals.languages = _.values(languages)
        next();
    },
    change: function(req, res) {
        var language = languages[req.query.code];
        if (language) {
            if (req.user) {
                req.user.language = language;
                db.updateUser({ language: language.code });

                // refresh the user info in the session
                req.session.passport.user = JSON.stringify(req.user);
            }
            else if (req.session) {
                req.session.language = language;
            }
        }

        res.json({});
    }
});