import {
    popup_notification,
    submit_with_screencover
} from '../../sb-admin/custom-assets/js/mjs/helpers.mjs';

$(document).ready(function(evt) {
    // Set the Look&Feel
    $("#id_env_selector").select2({
        closeOnSelect: true,
        placeholder: "Select a Salesforce Env",
        ajax: {
            url: get_env_list_url,
            type: 'GET',
            dataType: "json",
            data: function (params) {
                return {
                    search: params.term,
                }
            },
            processResults: function (response) {
                // Transforms the top-level key of the response object from 'items' to 'results'
                return response.payload;
            },
            error: function (response) {
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
            delay: 300
        }
    });

    // Constructs 'Dataflows' select2
    $("#id_dataflow_selector").select2({
        allowClear: true,
        closeOnSelect: true,
        placeholder: "Select a Dataflow",
        ajax: {
            url: get_dataflow_list_url,
            type: 'GET',
            dataType: "json",
            data: function (params) {
                // Query parameters will be ?search=[term]&type=public
                return {
                    search: params.term,
                    q: $('#id_env_selector').val(),
                    rc: $('#id_refresh')[0].checked,
                };
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

$('.btn-submit').on('click', (evt) => {
    let env_selector = $('#id_env_selector');

    if (env_selector.val() !== null) {
        let envname = env_selector.select2('data')[0].text,
            dfname = $('#id_dataflow_selector').select2('data')[0],
            progress_msg = "";

        dfname = ![null, "", undefined].includes(dfname) ? dfname.text : dfname;
        progress_msg = [null, "", undefined].includes(dfname) && $("#id_all")[0].checked ? `Downloading all dataflows from ${envname}.` :
            `Downloading ${dfname} from ${envname}.`;
        submit_with_screencover($('button[type="submit"]'), null, "Download Now?", progress_msg);
    } else {
        popup_notification("Warning", "Select at least one Salesforce Environment", 'warning');
    }
});