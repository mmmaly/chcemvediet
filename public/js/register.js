(function () {

    $(function() {
        $("button[type='submit']").click(register);

        $("input").blur(function () {
            $(this).popover("destroy");
        });
    });

    function register(event) {
        event.preventDefault();

        var data = validate();
        if (!data) return;

        $.ajax({
            type: "POST",
            url: "/register",
            dataType: "json",
            data: { user: data },
            success: function(result) {
                if (result.success) {
                    $("form :input").attr({ disabled: true });
                    $(".alert-success").show();
                }
                else if (result.error)
                    chcemvediet.reportError(result.error);
            }
        });
    }

    function validate() {
        var authToken = $("input[name='authToken']").val();
        var email, password, repeatPassword, firstName, lastName, street, city, zip;

        if (!(email = validateField("email", "Email missing")))
            return false;

        if (!authToken) {
            if (!(password = validateField("password", "Password missing")))
                return false;

            if (!(repeatPassword = validateField("repeat-password", "Password missing")))
                return false;

            if (password !== repeatPassword) {
                $("input[name='password']").focus()
                    .popover({ content: chcemvediet.strings["Password mismatch"] })
                    .popover("show");
                return false;
            }
        }

        if (!(firstName = validateField("firstName", "First name missing")))
            return false;

        if (!(lastName = validateField("lastName", "Last name missing")))
            return false;

        if (!(street = validateField("street", "Street missing")))
            return false;

        if (!(city = validateField("city", "City missing")))
            return false;

        if (!(zip = validateField("zip", "Zip missing")))
            return false;

        return {
            email: email,
            password: password,
            authToken: authToken,
            firstName: firstName,
            lastName: lastName,
            street: street,
            city: city,
            zip: zip
        };
    }

    function validateField(name, message) {
        var $field = $("input[name='" + name + "']");
        if (!$field.val()) {
            $field.focus()
                .popover({ content: chcemvediet.strings[message] })
                .popover("show");
            return false;
        }
        return $field.val();
    }

}());