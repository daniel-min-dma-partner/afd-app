import {
    popup_notification,
    submit_with_screencover
} from '../../sb-admin/custom-assets/js/mjs/helpers.mjs';

$("#proceed-deprecation").on('click', (evt) => {
    submit_with_screencover($('button[type="submit"]'), null, "Deprecate Now?", "Deprecation in progress.");
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
});