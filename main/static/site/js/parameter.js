import {
    popup_notification,
    submit_with_screencover,
    alert_if_required_missing
} from '../../sb-admin/custom-assets/js/mjs/helpers.mjs';


$(document).ready(function (evt) {

    // get JSON
    function getJson() {
        try {
            return JSON.parse($('#id_parameter').val().replaceAll("'", "\""));
        } catch (ex) {
            return "";
        }
    }

    // initialize
    var editor = new JsonEditor('#json-display', getJson());

    // enable translate button
    $("#id_parameter")
        .focus()
        .on('keyup', function () {
            editor.load(getJson());
        });

});

$("#proceed").on('click', (evt) => {
    let all_required_filled = alert_if_required_missing();

    if (all_required_filled) {
        submit_with_screencover($('button[type="submit"]'), null, "Are you sure?", "Saving...");
    }
});

