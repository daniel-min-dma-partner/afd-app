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

    $("#id_dataflow_selector").select2({
        ajax: {
            url: get_dataflow_list_url,
            type: 'GET',
            dataType: "json",
            data: function (params) {
                var query = {
                    search: params.term,
                    q: $('#id_env_selector').val(),
                }

                // Query parameters will be ?search=[term]&type=public
                return query;
            },
            processResults: function (response) {
                // Transforms the top-level key of the response object from 'items' to 'results'
                return response.payload;
            },
            error: function(response) {
                console.log(response.responseJSON);
            },
            minimumInputLength: 5,
            delay: 1000,
        }
    });
});

$("#id_env_selector").on('change', function() {
    $("#id_dataflow_selector").val('').trigger('change');
});

$("#id_dataflow_selector").on('change', function(evt) {
    if ($(this).val() !== null) {
        $("button.accordion-button").removeClass('collapsed').attr('disabled', false);;
        $("div.accordion-collapse").addClass('show');
        $('#myTextarea').html("");

        $.ajax({
            type: "GET",
            url: get_df_info_url,
            dataType: "json",
            data: {
                dataflow_id: $("#id_dataflow_selector").val(),
                env_pk: $("#id_env_selector").val(),
            },
            success: function(response) {
                console.log(response);
                $('#myTextarea').html(JSON.stringify(response.payload, undefined, 4));
            },
            error: function(response) {
                $("div.accordion-body").html(response.responseJSON);
            },
        });
    } else {
        $("button.accordion-button").addClass('collapsed').attr('disabled', true);
        $("div.accordion-collapse").removeClass('show');
    }
});