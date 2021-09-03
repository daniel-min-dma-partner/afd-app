import {popup_notification, submit_with_screencover, alert_if_required_missing} from '../../sb-admin/custom-assets/js/mjs/helpers.mjs';

// CRU is shorthand for 'CReate, Update'
let is_cru = window.location.href.includes("/profile/create") || window.location.href.includes("/profile/edit");

$(document).ready(function (evt) {
    if (is_cru) {
        $("#id_type").select2({
            closeOnSelect: true,
            placeholder: "Select an Option",
            allowClear: false,
            minimumResultsForSearch: -1,
            ajax: {
                url: type_list_url,
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

        $("#id_key").focus();
    }
});

if (is_cru) {
    $("#proceed").on('click', (evt) => {
        let all_required_filled = alert_if_required_missing();

        if (all_required_filled) {
            submit_with_screencover($('button[type="submit"]'), null, "Are you sure?", "Saving...");
        }
    });
}

if (!is_cru) {
    $(".delete-profile").on('click', function (evt) {
        if (confirm("Are you sure to delete the " + $(this).data('key') + "?")) {
            $.ajax({
                url: delete_url.replace("0000", $(this).data('pk')),
                success: function (response) {
                    location.reload();
                }
            });
        }
    });
}