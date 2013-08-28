var express = require("express"),
    jade = require("jade"),
    stylus = require("stylus"),
    i18n = require("i18n");

i18n.configure({
    locales: ["sk", "en"],
    directory: __dirname + "/private/locales"
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

    app.use(express.cookieParser());
    app.use(express.cookieSession({ secret: process.env.HEROKU_POSTGRESQL_ROSE_URL || "secret" }));
    app.use(i18n.init);
    app.use(app.router);
    app.use(express.static(__dirname + "/public"));
});

// TODO: just a test, shift routing to a separate file later
app.get("/", function (req, res) {
    res.setLocale("sk");
    res.render("index");
});

app.listen(process.env.PORT || 8080);