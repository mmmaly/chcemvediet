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

    chcemvediet.reportError = function(message)
    {
        $("#alert").html("<div class=\"alert alert-error fade in\">" +
            "<button type=\"button\" class=\"close\" data-dismiss=\"alert\">&times;</button>" +
            message + "</div>");

        setTimeout(function () { $("#alert .alert").alert("close"); }, 2000);
    }

}());