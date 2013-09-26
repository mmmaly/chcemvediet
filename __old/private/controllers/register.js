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

    // if available, pre-fill some fields from the provider
    var provider, authToken, email, firstName, lastName;

    var registrationInfo = req.session.registrationInfo;
    if (registrationInfo) {
        if (registrationInfo.google) {
            var profile = registrationInfo.google.profile;
            provider = "google";
            authToken = registrationInfo.google.identifier;
            email = profile.emails && profile.emails[0] && profile.emails[0].value;

            if (profile.name) {
                var name = profile.name;
                firstName = name.givenName;
                lastName = name.middleName ? name.middleName + " " + (name.familyName || "") : name.familyName;
            }
        }
        else if (registrationInfo.twitter) {
            var profile = registrationInfo.twitter.profile;
            provider = "twitter";
            authToken = registrationInfo.twitter.identifier;

            if (profile.displayName) {
                var names = profile.displayName.split(" ");
                firstName = names[0];
                lastName = names.slice(1).join(" ");
            }
        }
        else if (registrationInfo.facebook) {
            var profile = registrationInfo.facebook.profile;
            provider = "facebook";
            authToken = registrationInfo.facebook.identifier;

            if (profile.username)
                email = profile.username + "@facebook.com";

            if (profile.name) {
                var name = profile.name;
                firstName = name.givenName;
                lastName = name.middleName ? name.middleName + " " + (name.familyName || "") : name.familyName;
            }
        }

        delete req.session.registrationInfo;
    }

    res.render("register", {
        strings: JSON.stringify(strings),
        provider: provider,
        authToken: authToken,
        email: email || "",
        firstName: firstName || "",
        lastName : lastName || ""
    });
};

exports.post = function (req, res) {

    var user = req.body.user;

    if (!user.email || (!user.authToken && !user.password) || !user.firstName || !user.lastName || !user.street || !user.city || !user.zip)
        return res.json({ error: "Missing data from the form" });

    // replace the plain text password with its hash before saving into db
    if (user.password)
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