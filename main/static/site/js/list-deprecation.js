import {popup_notification} from "../../sb-admin/custom-assets/js/mjs/helpers.mjs";

$('.btn-show-diff').on('click', function (evt) {
    let pk = $(this).parent().parent().find('.pk').html();

    $.ajax({
        type: 'GET',
        url: show_diff_url,
        data: {
            pk: pk,
        },
        success: function(response) {
            location.reload();
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
    });
});