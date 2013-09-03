var index = require("./controllers/index"),
    login = require("./controllers/login"),
    whyRegister = require("./controllers/why-register");

exports.init = function(app) {
    app.get("/", index.render);
    app.get("/login", login.render);
    app.get("/why-register", whyRegister.render);
};