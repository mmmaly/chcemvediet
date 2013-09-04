var index = require("./controllers/index"),
    login = require("./controllers/login"),
    register = require("./controllers/register"),
    whyRegister = require("./controllers/why-register");

exports.init = function(app) {
    app.get("/", index.render);
    app.get("/login", login.render);
    app.get("/register", register.render);
    app.post("/register", register.post);
    app.get("/why-register", whyRegister.render);
};