(function () {

    $(function() {
        $("#obligees").selectize({
            valueField: 'id',
            labelField: 'name',
            searchField: 'name',
            options: [],
            create: false,
            render: {
                option: function(item, escape) {
                    return "<div>" +
                        "<div class='name'>" + escape(item.name) + "</div>" +
                        "<div class='address'>" +
                        escape(item.city) + ", " +
                        escape(item.street) + ", " +
                        escape(item.zip) + " " +
                        "</div></div>";
                }
            },
            load: loadObligees
        });
    });

    function loadObligees(query, callback) {
        if (!query.length) return callback();
        $.ajax({
            url: "/search/obligees",
            type: "GET",
            dataType: "json",
            data: { term: query },
            error: function() {
                callback();
            },
            success: function(res) {
                callback(res.obligees);
            }
        });
    }

}());