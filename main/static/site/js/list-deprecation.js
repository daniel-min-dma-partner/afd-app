import {popup_notification} from "../../sb-admin/custom-assets/js/mjs/helpers.mjs";

$('.btn-show-diff').on('click', function (evt) {
    let pk = $(this).parent().parent().find('.pk').val();
    console.log(pk);

    $.ajax({
        type: 'GET',
        url: show_diff_url,
        data: {
            pk: pk,
        },
        success: function (response) {
            location.reload();
        },
        error: function(response) {
            if (response.responseJSON !== null && response.responseJSON !== undefined) {
                if ('error' in response.responseJSON) {
                    popup_notification("Warning", response.responseJSON['error'], 'warning');
                } else {
                    popup_notification("Warning", JSON.stringify(response.responseJSON), 'warning');
                }
            } else {
                if (!(response.statusText in [null, '', undefined]) && response.statusText === 'abort') {
                    return false;
                }
                popup_notification("Warning", response.statusText, 'warning');
            }
        },
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