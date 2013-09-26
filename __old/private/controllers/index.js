var db = require("../db");

exports.render = function (req, res) {
    res.render("index");
};

exports.obligees = function (req, res) {
    db.findObligees(req.query.term, 10)
        .then(function (obligees) {
            res.json({ obligees: obligees });
        },
        function (err) {
            res.json({ error: "Obligees search failed" });
        });
};