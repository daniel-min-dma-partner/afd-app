import {popup_notification} from "../../sb-admin/custom-assets/js/mjs/helpers.mjs";

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