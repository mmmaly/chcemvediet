(function () {

    window.chcemvediet = window.chcemvediet || {};

    $(function() {
        $("#logout").click(logout);

        chcemvediet.strings = {};
        $(".strings").each(function () {
            $.extend(chcemvediet.strings, JSON.parse($(this).html()));
        });
    });

    function logout()
    {
        $.ajax({
            type: "POST",
            url: "/logout",
            success: function() {
                window.location.reload();
            }
        });
    }

    chcemvediet.reportError = function(message) {
        $("#alert").html("<div class=\"alert alert-error fade in\">" +
            "<button type=\"button\" class=\"close\" data-dismiss=\"alert\">&times;</button>" +
            message + "</div>");

        setTimeout(function () { $("#alert .alert").alert("close"); }, 2000);
    };

    chcemvediet.parseUri = function(str) {

        // parseUri 1.2.2
        // (c) Steven Levithan <stevenlevithan.com>
        // MIT License

        var o = {
            strictMode: false,
            key: ["source","protocol","authority","userInfo","user","password","host","port","relative","path","directory","file","query","anchor"],
            q:   {
                name:   "queryKey",
                parser: /(?:^|&)([^&=]*)=?([^&]*)/g
            },
            parser: {
                strict: /^(?:([^:\/?#]+):)?(?:\/\/((?:(([^:@]*)(?::([^:@]*))?)?@)?([^:\/?#]*)(?::(\d*))?))?((((?:[^?#\/]*\/)*)([^?#]*))(?:\?([^#]*))?(?:#(.*))?)/,
                loose:  /^(?:(?![^:@]+:[^:@\/]*@)([^:\/?#.]+):)?(?:\/\/)?((?:(([^:@]*)(?::([^:@]*))?)?@)?([^:\/?#]*)(?::(\d*))?)(((\/(?:[^?#](?![^?#\/]*\.[^?#\/.]+(?:[?#]|$)))*\/?)?([^?#\/]*))(?:\?([^#]*))?(?:#(.*))?)/
            }
        };

        var m   = o.parser[o.strictMode ? "strict" : "loose"].exec(str),
            uri = {},
            i   = 14;

        while (i--) uri[o.key[i]] = m[i] || "";

        uri[o.q.name] = {};
        uri[o.key[12]].replace(o.q.parser, function ($0, $1, $2) {
            if ($1) uri[o.q.name][$1] = $2;
        });

        return uri;
    };

}());