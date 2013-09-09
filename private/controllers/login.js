exports.render = function (req, res) {
    var strings = {
        "Google login failed": res.__("Google login failed"),
        "Twitter login failed": res.__("Twitter login failed")
    };

    res.render("login", {
        strings: JSON.stringify(strings)
    });
}