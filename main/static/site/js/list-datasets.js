import {jsonEditor, popup_notification, toast_remove} from '../../sb-admin/custom-assets/js/mjs/helpers.mjs';

$(document).ready(function (evt) {
    let editor = jsonEditor($('#json-holder')[0], $('#id_datasets'));
    let clipbtn = $('a.copy-to-clip');

    function update_editor(data = {}) {
        let template = JSON.parse(JSON.stringify(data));
        editor.set(template);
        clipbtn.attr('hidden', !template.length);
    }

    function get_datasets() {
        let form = $('form#dataset-list-form'),
            post_url = form.attr('action');

        $.ajax({
            url: post_url,
            type: "POST",
            data: new FormData(form[0]),

            // Tell jQuery not to process data or worry about content-type
            // You *must* include these options!
            cache: false,
            contentType: false,
            processData: false,

            // Custom XMLHttpRequest
            xhr: function () {
                var myXhr = $.ajaxSettings.xhr();
                if (myXhr.upload) {
                    // For handling the progress of the upload
                    myXhr.upload.addEventListener('progress', function (e) {
                        if (e.lengthComputable) {
                            $('progress').attr({
                                value: e.loaded,
                                max: e.total,
                            });
                        }
                    }, false);
                }
                return myXhr;
            },

            error: function (response) {
                update_editor({});
                clipbtn.attr('hidden', true);
            },

            success: function (response) {
                toast_remove();
                let datasets = response.datasets;
                update_editor(datasets);
            }
        });
    }

    // Dataflow file selector change
    $("input:file").change(function () {
        get_datasets();
    });

    // Clipboard Button
    clipbtn.on('click', function (evt) {
        evt.preventDefault();
        navigator.clipboard.writeText(JSON.stringify(editor.get()));
        popup_notification('Copy to Clipboard', "Copied successfully", 'success', true, 1000);
    });
});