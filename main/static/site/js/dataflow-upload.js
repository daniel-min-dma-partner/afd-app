import {block_screen} from '../../sb-admin/custom-assets/js/mjs/helpers.mjs';

$("#submit-modal-trigger").on('click', (evt) => {
    $('#dataflow').text($('#id_file').val());
    $('#sfdcOrg').text($('#id_env_selector').select2('data')[0].text);
});

$('#confirmation-proceed').on('click', (evt) => {
    if (confirm("Upload now?")) {
        $('#id_modal').modal('hide');
        block_screen();
        $('#submit-btn').click();
    } else {
        $('#id_modal').modal('hide');
        block_screen('hide');
    }
});