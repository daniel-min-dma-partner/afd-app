import {
    popup_notification,
    submit_with_screencover,
    alert_if_required_missing
} from '../../sb-admin/custom-assets/js/mjs/helpers.mjs';


$(document).ready(function (evt) {
    let container = document.getElementById("parameter-editor");

    if (container) {
        let options = {
            mainMenuBar: mainMenuBar,
            modes: modes,
            search: false,

            onChange: function (evt) {
                try {
                    let json = editor.get();
                    document.getElementById("id_parameter").value = $.trim(JSON.stringify(json));
                } catch (error) {
                    return false;
                }
            },

            onModeChange: function (endMode, oldMode) {
                if (endMode === 'tree') {
                    editor.expandAll();
                }
            },
        };

        let editor = new JSONEditor(container, options);
        let json = JSON.parse($.trim($('#id_parameter').html()));
        editor.set(json);

        if (expandAll) {
            editor.expandAll();
        }
    }
});

$("#proceed").on('click', (evt) => {
    let all_required_filled = alert_if_required_missing();

    if (all_required_filled) {
        submit_with_screencover($('button[type="submit"]'), null, "Are you sure?", "Saving...");
    }
});

$('.delete-parameter').on('click', function (evt) {
    if (confirm("Are you sure?") === true) {
        $("#delete-parameter")[0].click();
    }
});