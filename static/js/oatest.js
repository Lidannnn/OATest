/**
 * Created by songbowen on 9/30/2015.
 */

/**
 * search.html
 */
$("#info-modal").on("show.bs.modal", function(event) {
    var btn = $(event.relatedTarget);
    var date = btn.data("date");
    var modal = $(this);
    modal.find(".modal-body form")[0].reset();

    $.getJSON("/attence/info/?check-date=" + date, function(data) {
        modal.find("#checkin-time").val(data.checkin || data.checkout || date+" 00:00:00");
        modal.find("#checkout-time").val(data.checkout || data.checkin || date+" 00:00:00");
        modal.find("#check-date").val(date);
        modal.find("#info").val(data.info);
        if(data.status === "lock") {
            modal.find(".modal-body button").attr("disabled", "disable");
            modal.find("input").attr("readonly", "readonly");
            modal.find("textarea").attr("readonly", "readonly");
            modal.find("label input").attr("disabled", "disabled")
        } else {
            modal.find(".modal-body button").removeAttr("disabled");
            modal.find("input").removeAttr("readonly");
            modal.find("textarea").removeAttr("readonly");
            modal.find("label input").removeAttr("disabled");
        }
    });
});
$("#info-form").on("submit", function(event) {
    event.preventDefault();
    var check_in = $("#checkin-time");
    var check_out = $("#checkout-time");
    if(!/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(check_in.val())) {
        alert("上班时间格式错误！");
        check_in.parent().addClass("has-error");
        return false;
    } else {
        check_in.parent().removeClass("has-error");
    }
    if(!/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(check_out.val())) {
        alert("下班时间格式错误！");
        check_out.parent().addClass("has-error");
        return false
    } else {
        check_out.parent().removeClass("has-error");
    }
    $.ajax({
        url: "/attence/submit_info/",
        method: "POST",
        data: $("#info-form").serialize(),
        success: function(data) {
            alert("Done");
            $("#info-modal").modal("hide");
        },
        error: function(data) {
            alert(data);
        }
    })
});

/**
 * index.html
 */
$("#btn-checkin").on("click", function(event) {
    $.ajax({
        url: "/attence/checkin/",
        method: "POST",
        success: function (data) {
            if(data != "ok") {
                alert(data);
            } else {
                location.reload();
            }
        },
        error: function(data) {
            alert(data);
        }
    })
});
$("#btn-checkout").on("click", function(event) {
    $.ajax({
        url: "/attence/checkout/",
        method: "POST",
        success: function (data) {
            if(data != "ok") {
                alert(data);
            } else {
                location.reload();
            }
        },
        error: function(data) {
            alert(data);
        }
    })
});

/**
 * register.html
 */
$("#user-email").blur(function() {
    var email_input = $(this);
    var email = email_input.val();
    if(!/^\w+_?\w+$/i.test(email)) {
        $(".btn-primary").attr("disabled", "disabled");
        email_input.parent().addClass("has-error");
        alert("格式错误！")
    } else {
        $(".btn-primary").removeAttr("disabled");
        email_input.parent().removeClass("has-error");
    }
});