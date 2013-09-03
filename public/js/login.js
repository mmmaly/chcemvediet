(function () {

    $(function() {
        $("button[type='submit']").click(login);
    });

    function login(event)
    {
        event.preventDefault();

        $.ajax({
            type: "POST",
            url: "/login",
            dataType: "json",
            data: {
                authMethod: "local",
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