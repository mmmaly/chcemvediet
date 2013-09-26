var express = require("express"),
    jade = require("jade"),
    stylus = require("stylus"),
    i18n = require("i18n"),
    passport = require("passport"),
    languages = require("./private/locales/languages");

i18n.configure({
    locales: languages.locales,
    directory: __dirname + "/private/locales",
    updateFiles: false
});

var app = express();

app.configure(function () {
    app.set("url", process.env.APP_URL || "https://chcemvediet.herokuapp.com")

    app.set("view engine", "jade");
    app.set("views", __dirname + "/views");
    app.engine("html", jade.__express);
    app.use(stylus.middleware({
        src: __dirname + "/views",
        dest: __dirname + "/public"
    }));
    app.use(i18n.init);

    app.use(express.static(__dirname + "/public"));
    app.use(express.cookieParser());
    app.use(express.bodyParser());
    app.use(express.session({ secret: process.env.DATABASE_URL || "secret" }));
    app.use(passport.initialize());
    app.use(passport.session());

    app.use(languages.process);
    app.use(app.router);
});

// initialize authentication
require("./private/authentication").init(app);

// initialize all the routes
require("./private/router").init(app);

app.listen(process.env.PORT || 8080);