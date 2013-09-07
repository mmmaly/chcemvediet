exports.render = function (req, res) {
    var strings = {
        "Google login failed": res.__("Google login failed")
    };

    res.render("login", {
        strings: JSON.stringify(strings)
    });
}