import {
    popup_notification,
    submit_with_screencover,
    alert_if_required_missing
} from '../../sb-admin/custom-assets/js/mjs/helpers.mjs';

$(document).ready(function (evt) {
    $('#id_title').focus();
});

$("#proceed").on('click', (evt) => {
    let all_required_filled = alert_if_required_missing();

    if (all_required_filled) {
        submit_with_screencover($('button[type="submit"]'), null, "Are you sure?", "Saving...");
    }
});

$(".delete-release").on('click', function (evt) {
    let url = $(this).data('url');

    if (confirm("Are you sure to delete this release?")) {
        $('#delete-release')[0].click();
    }
});
