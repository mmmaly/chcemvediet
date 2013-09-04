var db = require("../db"),
    crypto = require("crypto");

exports.render = function (req, res) {

    // todo: some helper and grouping mechanism for the strings

    var strings = {
        "Email missing": res.__("Email missing"),
        "Password missing": res.__("Password missing"),
        "Password mismatch": res.__("Password mismatch"),
        "First name missing": res.__("First name missing"),
        "Last name missing": res.__("Last name missing"),
        "Street missing": res.__("Street missing"),
        "City missing": res.__("City missing"),
        "Zip missing": res.__( "Zip missing")
    };

    res.render("register", {
        strings: JSON.stringify(strings)
    });
};

exports.post = function (req, res) {

    var user = req.body.user;

    if (!user.email || !user.password || !user.firstName || !user.lastName || !user.street || !user.city || !user.zip)
        return res.json({ error: "Missing data from the form" });

    // replace the plain text password with its hash before saving into db
    user.password = crypto.createHash('md5').update(user.password).digest("hex");

    db.getUser(user.email)
        .then(function(duplicate) {
            if (duplicate)
                throw res.json({ error: res.__("Email already in use") });
        }, handleError)
        .then(function() { return db.createUser(user); })
        .then(function () {
            return res.json({ success: true });
        }, handleError);

    function handleError(err) {
        if (err !== res)
            res.json({ error: res.__("Registration error") });
    }
};