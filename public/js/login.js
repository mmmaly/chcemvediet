(function () {

    $(function() {
        $("button[type='submit']").click(login);

        if (location.search.indexOf("fail=google") >= 0)
            chcemvediet.reportError(chcemvediet.strings["Google login failed"]);

        if (location.search.indexOf("fail=twitter") >= 0)
            chcemvediet.reportError(chcemvediet.strings["Twitter login failed"]);
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