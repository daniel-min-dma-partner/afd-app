import {
    popup_notification,
    submit_with_screencover
} from '../../sb-admin/custom-assets/js/mjs/helpers.mjs';

$("#proceed-deprecation").on('click', (evt) => {
    submit_with_screencover($('button[type="submit"]'), null, "Deprecate Now?", "Deprecation in progress.");
});