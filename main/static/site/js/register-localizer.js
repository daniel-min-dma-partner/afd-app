import {jsonEditor, popup_notification, toast_remove} from '../../sb-admin/custom-assets/js/mjs/helpers.mjs';

$(document).ready(function (evt) {
    let editor = jsonEditor($('#json-holder')[0], $('#id_registers'));

    function update_editor(registers = {}) {
        let template = JSON.parse(JSON.stringify(registers));
        editor.set(template);
    }

    $('button.locate-register').on('click', function (evt) {
        evt.preventDefault();

        let form = $('form#register-locator-form'),
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
                if (![null, undefined, false].includes(response.responseJSON)) {
                    if ('error' in response.responseJSON) {
                        popup_notification("Warning", response.responseJSON.error, 'warning');
                    }
                }
            },

            success: function (response) {
                toast_remove();
                let registers = response.registers;
                update_editor(registers);
            }
        });
    });

    $('#id-node').change(function (evt) {

    });
});