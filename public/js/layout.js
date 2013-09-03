(function () {

    window.chcemvediet = window.chcemvediet || {};

    $(function() {
        $("#logout").click(logout);
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