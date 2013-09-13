var authentication = require("./authentication"),
	index = require("./controllers/index"),
    login = require("./controllers/login"),
    register = require("./controllers/register"),
    whyRegister = require("./controllers/why-register"),
    languages = require("./locales/languages");

exports.init = function(app) {
    app.get("/", index.render);
	app.get("/login", login.render);

	app.post("/login", authentication.login.local);
    app.post("/logout", authentication.logout);
    app.get("/login/google", authentication.login.google.init);
    app.get("/login/google/return", authentication.login.google["return"]);
    app.get("/login/twitter", authentication.login.twitter.init);
    app.get("/login/twitter/return", authentication.login.twitter["return"]);
    app.get("/login/facebook", authentication.login.facebook.init);
    app.get("/login/facebook/return", authentication.login.facebook["return"]);
    app.get("/register/google", authentication.register.google.init);
    app.get("/register/google/return", authentication.register.google["return"]);
    app.get("/register/twitter", authentication.register.twitter.init);
    app.get("/register/twitter/return", authentication.register.twitter["return"]);
    app.get("/register/facebook", authentication.register.facebook.init);
    app.get("/register/facebook/return", authentication.register.facebook["return"]);

    app.get("/register", register.render);
    app.post("/register", register.post);
    app.get("/why-register", whyRegister.render);

    app.post("/change-language", languages.change);
};