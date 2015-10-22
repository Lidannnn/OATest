/**
 * Created by songbowen on 10/4/2015.
 */

/**
 * user_manage.html
 */
$(".btn-view-attence").on("click", function(event) {
    var btn = $(event.target);
    location.href = "/admin/user/" + btn.data("uid");
});

$(".btn-dismiss").on("click", function(event) {
    var btn = $(event.target);
    if(confirm("Sure?")) {
        $.ajax({
            url: "/admin/user/" + btn.data("uid"),
            method: "DELETE",
            success: function (data) {
                if(data != "ok") {
                    alert(data);
                } else {
                    location.reload();
                }
            },
            error: function (data) {
                alert(data);
            }
        });
    } else {
        alert("careful next time!");
    }
});

/**
 * attendance_manage.html
 */
$(".btn-pass").on("click", function(event) {
    var btn = $(event.target);
    var check_date = btn.data("check_date");
    var maid = btn.data("maid");
    $.ajax({
        url: "/admin/attence/" + maid,
        method: "POST",
        data: {
            "check-date": check_date,
            "action": "pass"
        },
        success: function (data) {
            if(data != "ok") {
                alert(data);
            } else {
                location.reload();
            }
        },
        error: function (data) {
            alert(data);
        }
    })
});
$(".btn-reject").on("click", function(event) {
    var btn = $(event.target);
    var check_date = btn.data("check_date");
    var maid = btn.data("maid");
    $.ajax({
        url: "/admin/attence/" + maid,
        method: "POST",
        data: {
            "check-date": check_date,
            "action": "reject"
        },
        success: function (data) {
            if(data != "ok") {
                alert(data);
            } else {
                location.reload();
            }
        },
        error: function (data) {
            alert(data);
        }
    })
});