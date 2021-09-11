import {
    popup_notification,
    submit_with_screencover,
    alert_if_required_missing
} from '../../sb-admin/custom-assets/js/mjs/helpers.mjs';


$(document).ready(function (evt) {
    let container = document.getElementById("parameter-editor");

    if (container) {
        // UI options.
        let options = {
            mainMenuBar: mainMenuBar,
            modes: modes,
            search: false,
        };

        // Converts strings to HTML tag.
        let json = JSON.parse($.trim($('#id_parameter').html()));
        let text = {};
        if (![undefined, null, ""].includes(json['profile-guidelines'])) {
            text = json['profile-guidelines'][0]['text'];
            json['profile-guidelines'][0]['text'] = jQuery('<div />').html(text).text();
        }

        // Set data.
        let editor = new JSONEditor(container, options);
        editor.set(json);

        // Event setup.
        editor.options.onModeChange = function (endMode, oldMode) {
            if (endMode === 'tree') {
                editor.expandAll();
            }
        };
        editor.options.onChange = function (evt) {
            try {
                let json = editor.get();
                document.getElementById("id_parameter").value = $.trim(JSON.stringify(json));
            } catch (error) {
                return false;
            }
        };

        // Initial expansion method.
        if (expandAll) {
            if (mode === 'tree') {
                editor.expandAll();
            }
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