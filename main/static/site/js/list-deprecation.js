import {popup_notification, show_screenplay} from "../../sb-admin/custom-assets/js/mjs/helpers.mjs";

$(document).ready(function (evt) {
    let dataTable = $("#dataTable").DataTable({
        "lengthMenu": [[10, 25, 50, -1], [10, 25, 50, "All"]],
        "order": [[ 0, "desc" ]],
    });
    // #myInput is a <input type="text"> element
    $('input[type="search"]').on('keyup', function () {
        dataTable.search( this.value.trim() ).draw();
    });

    // dataTable = $("#df-list-table").DataTable({searching: false, paging: false, info: false});

    let containers = document.getElementsByClassName("parameter-editor-div");

    $.each(containers, (index, element) => {
        let container = $(element),
            pk = container.data('pk');

        // UI options.
        let options = {
            mainMenuBar: true,
            mode: 'tree',
            search: true,
        };

        // Converts strings to HTML tag.
        let json = JSON.parse($.trim($(`#id_parameter-${pk}`).html()));

        // Set data.
        let editor = new JSONEditor(element, options);
        editor.set(json);
        editor.expandAll();
    });

    containers = document.getElementsByClassName("removed-fields-div");

    $.each(containers, (index, element) => {
        let container = $(element),
            pk = container.data('pk');

        // UI options.
        let options = {
            mainMenuBar: true,
            mode: 'form',
            search: true,
        };

        // Converts strings to HTML tag.
        let json = JSON.parse($.trim($(`textarea#removedfields-${pk}`).html()));

        // Set data.
        let editor = new JSONEditor(element, options);
        editor.set(json);
        editor.expandAll();
    });

    containers = document.getElementsByClassName("registers-div");

    $.each(containers, (index, element) => {
        let container = $(element),
            pk = container.data('pk');

        // UI options.
        let options = {
            mainMenuBar: true,
            mode: 'form',
            search: true,
        };

        // Converts strings to HTML tag.
        let json = JSON.parse($.trim($(`textarea#registers-${pk}`).html()));

        // Set data.
        let editor = new JSONEditor(element, options);
        editor.set(json);
        editor.expandAll();
    });

    // Removes screen cover after loading jqueries.
    show_screenplay(0, "", true);

    $('#days').focus().select();
});

$('.btn-remove-deprec').on('click', function () {
    let modal_body = $('#delete-confirmation-md .modal-body');
    modal_body.find('input[id="id-field"]').val($(this).data('id')).trigger('change');
    modal_body.find('input[id="name-field"]').val($(this).data('model-name')).trigger('change');
});

$('#delete-confirmation-md').on('shown.bs.modal', function (e) {
    $(this).find('button[id^="delete-btn"]').focus();
});

$('button.reset-filter').on('click', function () {
    $(this).parent().parent().find('input.form-check-input').each((ind, element) => {
        if (element.checked) {
            $(element).click();
        }
    });
});

$('button.download-selected-clicker').on('click', function (evt) {
    let pk = $(this).data('pk'),
        only_dep = $(`#deprecation-filter-${pk}`)[0].checked,
        errors = $(`#deprecation-only-errors-${pk}`)[0].checked;

    $(`button.download-selected-${pk}`).click();
});

$('button.download-selected').on('click', function (evt) {
    let pk = $(this).data('pk'),
        only_dep = $(`#deprecation-filter-${pk}`)[0].checked,
        errors = $(`#deprecation-only-errors-${pk}`)[0].checked,
        no_changes = $(`#deprecation-no-changes-${pk}`)[0].checked,
        dep_name = $(this).data('name');

    if (!(only_dep || errors || no_changes)) {
        popup_notification("Information", "First select one of the checkbox option and then click again.", "info", true, 5000);
    } else if (only_dep+errors+no_changes > 1) {
        popup_notification("Warning", "Select only one option to download.", "warning", true, 5000);
    } else {
        if (confirm('Are you sure?')) {
            let request = new XMLHttpRequest(),
                url = download_selected_dfs.replace('xxx', only_dep)
                    .replace('yyy', errors)
                    .replace('zzz', no_changes)
                    .replace('0', pk),
                filename = only_dep ? 'Only Deprecated' : (errors ? "With Errors" : "No Deprecated");

            filename = `${filename} of ${dep_name}`;
            request.open('GET', url, true);
            request.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8');
            request.responseType = 'blob';

            request.onload = function (e) {
                if (this.status === 200) {
                    let blob = this.response;
                    let downloadLink = window.document.createElement('a');
                    let contentTypeHeader = request.getResponseHeader("Content-Type");
                    downloadLink.href = window.URL.createObjectURL(new Blob([blob], {type: contentTypeHeader}));
                    downloadLink.download = `${filename}.zip`;
                    document.body.appendChild(downloadLink);
                    downloadLink.click();
                    document.body.removeChild(downloadLink);
                } else {
                    if (this.responseJSON !== null && this.responseJSON !== undefined) {
                        if ('error' in this.responseJSON) {
                            popup_notification("Warning", this.responseJSON['error'], 'warning');
                        } else {
                            popup_notification("Warning", JSON.stringify(this.responseJSON), 'warning');
                        }
                    } else {
                        if (!(this.statusText in [null, '', undefined]) && this.statusText === 'abort') {
                            return false;
                        }
                        popup_notification("Warning", this.statusText, 'warning');
                    }
                }
            };
            request.onerror = function (response) {
                location.reload();
            };
            request.send();
        }
    }
});

$(".delete-all").on('click', function (evt) {
    if (confirm("Do you want to delete ALL Deprecations at Once?")) {
        $.ajax({
            url: delete_all_url,
            type: "GET",
            success: function (response) {
                location.reload();
            }
        });
    }
});

$('div[id^="object_fields_"]').on('shown.bs.collapse', function () {
    let this_ = $(this),
        pk = this_.data('pk'),
        detail_div = $(`#collapseExample_${pk}`),
        name = this_.data('name');

    if (detail_div && detail_div.hasClass('show')) {
        // $('.title-' + pk).append(name);
        $(`a[class="name-${pk}"]`)[0].click();
    } else {
        $('.title-' + pk).empty();
    }
});

$('div[id^="collapseExample_"]').on('shown.bs.collapse', function () {
    let this_ = $(this),
        pk = this_.data('pk'),
        of_div = $(`#object_fields_${pk}`),
        name = this_.data('name');

    if (of_div && of_div.hasClass('show')) {
        // $('.title-' + pk).append(name);
        $(`a.of-${pk}`)[0].click();
    } else {
        $('.title-' + pk).empty();
    }
});

$('a.h5').click(function (evt) {
    let pk = $(this).data('pk');
    $(`a.removed-fields-${pk}`)[0].click();
});

$('.to-clip').click(function (evt) {
    let pk = $(this).data('pk'),
        kind = $(this).data('kind'),  // removedfields | registers
        editor = $(`textarea#${kind}-${pk}`),
        json_object = JSON.parse(editor.val()),
        for_clipboard = $.map(json_object, function(value, key) {
            return kind === 'registers' ? value['dataset-alias'] : $.map(value, function (field) {
                return `${key}.${field}`;
            });
        });
    for_clipboard.sort();
    navigator.clipboard.writeText(for_clipboard.join('\n'));
    kind = kind === "registers" ? "datasets" : kind;
    popup_notification('To Clipboard', `List of <code>${kind}</code> copied successfully to clipboard.`, 'success', true, 1600);
});

$('#days').on('change', function (evt) {
    $('form#list-filter').submit();
}).on('keypress', function (evt) {
    let key = evt.which;
    if (key === 13) {
        evt.preventDefault();
        $('form#list-filter').submit();
    }
});