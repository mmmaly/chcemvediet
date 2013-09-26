(function () {

    $(function() {
        $("button[type='submit']").click(login);

        var uri = chcemvediet.parseUri(location);
        if (uri.queryKey && uri.queryKey.fail)
            chcemvediet.reportError(chcemvediet.strings["Provider login failed"].replace("{0}", uri.queryKey.fail));
    });

    function login(event)
    {
        event.preventDefault();

        $.ajax({
            type: "POST",
            url: "/login",
            dataType: "json",
            data: {
                username: $("[name='email']").val(),
                password: $("[name='password']").val()
            },
            success: function(data) {
                if (data.success)
                    window.location.href = "/";
                else if (data.error)
                    chcemvediet.reportError(data.error);
            }
        });
    }

}());