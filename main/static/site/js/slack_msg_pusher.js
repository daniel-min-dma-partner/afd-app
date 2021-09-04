import {popup_notification} from "../../sb-admin/custom-assets/js/mjs/helpers.mjs";

$(document).ready((evt) => {
    $("#id_slack_target").select2({
        allowClear: true,
        closeOnSelect: true,
        placeholder: "Select a SF Slack user/channel",
        ajax: {
            url: targetlist_url,
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
            delay: 300,
        }
    });
});

$("#" + has_manager_approval_field_id).on('change', function (evt) {
    enable_manager_name_field();
});

const enable_manager_name_field = () => {
    let is_checked = $("#" + has_manager_approval_field_id).get(0).checked;

    $("#" + manager_name_field_id).prop('readonly', !is_checked);
    $("#" + manager_name_field_id).val('').trigger('change');
};