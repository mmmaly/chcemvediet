var express = require("express"),
    jade = require("jade"),
    stylus = require("stylus"),
    i18n = require("i18n"),
    passport = require("passport");

i18n.configure({
    locales: ["sk", "en"],
    directory: __dirname + "/private/locales",
    updateFiles: false
});

var app = express();

app.configure(function () {
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

    app.use(function(req, res, next){
        res.setLocale(req.user && req.user.language || "sk");

        // for use in the jade templates
        res.locals.user = req.user;
        next();
    });

    app.use(app.router);
});

// initialize authentication
require("./private/authentication").init(app);

// initialize all the routes
require("./private/router").init(app);

app.listen(process.env.PORT || 8080);