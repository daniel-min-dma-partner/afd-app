import {
    popup_notification,
    submit_with_screencover,
    alert_if_required_missing
} from '../../sb-admin/custom-assets/js/mjs/helpers.mjs';

$("#proceed").on('click', (evt) => {
    let all_required_filled = alert_if_required_missing();

    if (all_required_filled) {
        submit_with_screencover($('button[type="submit"]'), null, "Are you sure?", "Saving...");
    }
});
