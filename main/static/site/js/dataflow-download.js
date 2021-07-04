import {popup_notification} from '../../sb-admin/custom-assets/js/mjs/helpers.mjs';

$(document).ready(function(evt) {
    // Constructs 'Environment' select2
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
            popup_notification("Warning", response.responseJSON['error'], "warning");
        }
    });

    // Constructs 'Dataflows' select2
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
                popup_notification("Warning", response.responseJSON['error'], 'warning');
            },
            minimumInputLength: 5,
            delay: 1000,
        }
    });
});

// Clears 'Dataflows' when 'Environment' changes
$("#id_env_selector").on('change', function() {
    $("#id_dataflow_selector").val('').trigger('change');
});

// Shows detailed-information of the selected dataflow from 'Dataflows'
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
                $('#myTextarea').html(JSON.stringify(response.payload, undefined, 4));
            },
            error: function(response) {
                console.log(response);
                popup_notification("Warning", response.responseJSON['error'], "warning");
            },
        });
    } else {
        $("button.accordion-button").addClass('collapsed').attr('disabled', true);
        $("div.accordion-collapse").removeClass('show');
    }
});