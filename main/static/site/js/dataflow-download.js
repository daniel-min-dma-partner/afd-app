$(document).ready(function(evt) {
    $.ajax({
        type: 'GET',
        url: get_env_list_url,
        success: function (response) {
            let option = "";
            $.each(response.payload, function(key, value) {
                option = $('<option></option>').attr("value", value[0]).text(value[1]);
                $("#id_env_selector").append(option);
            });
        },
        error: function (response) {
            console.log(response);
        }
    });
});

$("#id_env_selector").on('change', function(evt) {
    let env_selector = $(this),
        dataflow_selector = $("#id_dataflow_selector");

    dataflow_selector.prop('disabled', true);

    $.ajax({
        type: 'GET',
        url: get_dataflow_list_url,
        data: {
            env_pk: env_selector.val(),
        },
        success: function (response) {
            let option = "";

            $.each(response.payload, function(key, value) {
                option = $('<option></option>').attr("value", key).text(value);
                $("#id_dataflow_selector").append(option);
            });

            dataflow_selector.prop('disabled', false);
        },
        error: function (response) {
            console.log(response.responseJSON);
            location.reload();
        }
    })
});