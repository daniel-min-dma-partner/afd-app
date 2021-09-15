import {popup_notification} from "../../sb-admin/custom-assets/js/mjs/helpers.mjs";

$(document).ready(function (evt) {
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
        let text = {};
        if (![undefined, null, ""].includes(json['profile-guidelines'])) {
            text = json['profile-guidelines'][0]['text'];
            json['profile-guidelines'][0]['text'] = jQuery('<div />').html(text).text();
        }

        // Set data.
        let editor = new JSONEditor(element, options);
        editor.set(json);
        editor.expandAll();
    });
});

$('.btn-remove-deprec').on('click', function () {
    $('#delete-confirmation-md .modal-body').find('input[id="id-field"]').val($(this).data('id')).trigger('change');
    $('#delete-confirmation-md .modal-body').find('input[id="name-field"]').val($(this).data('model-name')).trigger('change');
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

$('button.download-selected').on('click', function (evt) {
    alert("To be implemented soon");

    // var request = new XMLHttpRequest();
    // request.open('POST', download_selected_dfs, true);
    // request.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8');
    // request.responseType = 'blob';
    //
    // request.onload = function (e) {
    //     if (this.status === 200) {
    //         var blob = this.response;
    //
    //         var downloadLink = window.document.createElement('a');
    //         var contentTypeHeader = request.getResponseHeader("Content-Type");
    //         downloadLink.href = window.URL.createObjectURL(new Blob([blob], {type: contentTypeHeader}));
    //         downloadLink.download = "che.zip";
    //         document.body.appendChild(downloadLink);
    //         downloadLink.click();
    //         document.body.removeChild(downloadLink);
    //     }
    // };
    // request.send(JSON.stringify({"a": "mongo"}));
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
//
// $('div.collapse').on('hide.bs.collapse', function (evt) {
//     $('div.details-divider').empty();
// });
//
$('tr[id^="object_fields_"]').on('shown.bs.collapse', function () {
    let this_ = $(this),
        detail_div = this_.parent().find('.detail'),
        name = this_.data('name'),
        pk = this_.data('pk');

    if (detail_div && detail_div.hasClass('show')) {
        // $('.title-' + pk).append(name);
        $(`a[class="name-${pk}"]`)[0].click();
    } else {
        $('.title-' + pk).empty();
    }
});

$('tr[id^="collapseExample_"]').on('shown.bs.collapse', function () {
    let this_ = $(this),
        of_div = this_.parent().find('.object-fields'),
        name = this_.data('name'),
        pk = this_.data('pk');

    if (of_div && of_div.hasClass('show')) {
        // $('.title-' + pk).append(name);
        $(`a.of-${pk}`)[0].click();
    } else {
        $('.title-' + pk).empty();
    }
});