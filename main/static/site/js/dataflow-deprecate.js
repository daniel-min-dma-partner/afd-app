import {
    popup_notification,
    submit_with_screencover,
    alert_if_required_missing
} from '../../sb-admin/custom-assets/js/mjs/helpers.mjs';

$(document).ready(function (evt) {
    $('#id_name').focus();
});

$("#proceed-deprecation").on('click', (evt) => {
    let required_fields_completed = alert_if_required_missing();

    if (required_fields_completed) {
        submit_with_screencover($('button[type="submit"]'), null, "Deprecate Now?", "Deprecation in progress.");
    }
});

$('#id_from_file').on('click', function (evt) {
    let is_from_file = this.checked,
        save_metadata = $("#id_save_metadata");

    $("#id_file").prop('disabled', !is_from_file).val('').trigger('change');
    $("#id_sobjects").prop('disabled', is_from_file).val('').trigger('change');
    $("#id_fields").prop('disabled', is_from_file).val('').trigger('change');

    if (save_metadata[0].checked) {
        save_metadata.click();
    }

    if (is_from_file) {
        $("#id_sobjects").siblings('label').removeClass('required');
        $("#id_fields").siblings('label').removeClass('required');
    } else {
        $("#id_sobjects").siblings('label').addClass('required');
        $("#id_fields").siblings('label').addClass('required');
    }
});