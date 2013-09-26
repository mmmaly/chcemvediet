exports.render = function (req, res) {
    var strings = {
        "Provider login failed": res.__("Provider login failed")
    };

    res.render("login", {
        strings: JSON.stringify(strings)
    });
};