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
                    rc: $('#id_refresh')[0].checked,
                }

                // Query parameters will be ?search=[term]&type=public
                return query;
            },
            processResults: function (response) {
                // Transforms the top-level key of the response object from 'items' to 'results'
                return response.payload;
            },
            error: function(response) {
                if (response.responseJSON !== null && response.responseJSON !== undefined) {
                    if ('error' in response.responseJSON) {
                        popup_notification("Warning", response.responseJSON['error'], 'warning');
                    } else {
                        popup_notification("Warning", JSON.stringify(response.responseJSON), 'warning');
                    }
                } else {
                    if (!(response.statusText in [null, '', undefined]) && response.statusText === 'abort') {
                        return false;
                    }
                    popup_notification("Warning", response.statusText, 'warning');
                }
            },
            minimumInputLength: 5,
            delay: 900,
        }
    });
});

// Clears 'Dataflows' when 'Environment' changes
$("#id_env_selector").on('change', function() {
    $("#id_dataflow_selector").val('').trigger('change');
});