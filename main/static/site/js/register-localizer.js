import {jsonEditor, popup_notification, toast_remove} from '../../sb-admin/custom-assets/js/mjs/helpers.mjs';

$(document).ready(function (evt) {
    let editor = jsonEditor($('#json-holder')[0], $('#id_registers'));

    function update_editor(registers = {}) {
        let template = JSON.parse(JSON.stringify(registers));
        editor.set(template);
    }

    const disable_clipboard = () => {
        $('button.clipboard').attr('disabled', true);
    };

    const enable_clipboard = () => {
        $('button.clipboard').removeAttr('disabled');
    };

    function get_registers() {
        disable_clipboard();

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
                enable_clipboard();
            }
        });
    }

    $("input:file").change(function () {
        update_editor({});

        $.ajax({
            url: list_node_url,
            type: "POST",
            data: new FormData($('form#register-locator-form')[0]),

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
                let nodes = response.nodes,
                    node_field = $('#id-node');

                node_field.find('option').remove();

                $.each(nodes, function (i, e) {
                    node_field.append(new Option(e, e));
                });
            }
        });
    });

    $("#id-node").select2({
        allowClear: true,
        closeOnSelect: true,
        placeholder: "Select a node",
    }).on('change', function (evt) {
        get_registers();
    });

    $('#id-complement').on('change', function (evt) {
        get_registers();
    });

    $('#id-datasets').on('keyup focusout', function (evt) {
        let usr_input = $(this).val();

        usr_input = usr_input.replaceAll('\n\n', '\n');
        usr_input = usr_input.split('\n').map(element => {
            return element.trim();
        }).filter(element => {
            return ![false, undefined, null, '', '\n'].includes(element);
        }).join('\n');
        $(this).val(usr_input).trigger('change');
    }).on('change', function (evt) {
        get_registers();
    });

    $('button.clipboard').click(function (evt) {
        evt.preventDefault();
        navigator.clipboard.writeText(JSON.stringify(editor.get()));
        popup_notification('Copy to Clipboard', "Copied successfully", 'success', true, 1000);
    });
});