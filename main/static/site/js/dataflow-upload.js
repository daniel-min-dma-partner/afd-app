import {block_screen, progress_loader} from '../../sb-admin/custom-assets/js/mjs/helpers.mjs';

$('#id_file').on('change', (evt) => {
    selected_df_name = evt.target.files[0].name;
});

$("#submit-modal-trigger").on('click', (evt) => {
    let envname = $('#id_env_selector').select2('data')[0].text,
        dfname = selected_df_name;
    envname = envname === 'Select One' ? "" : '<code>' + envname + '</code>';
    dfname = [null, "", undefined].includes(dfname) ? "" : '<code>' + dfname + '</code>';

    $('#dataflow').append(dfname);
    $('#sfdcOrg').append(envname);
});

$('#confirmation-proceed').on('click', (evt) => {
    if (confirm("Upload now?")) {
        $('#id_modal').modal('hide');
        block_screen();
        progress_loader(`Uploading ${$('#dataflow').text()} to ${$('#sfdcOrg').text()}`);
        $('#submit-btn').click();
    } else {
        $('#id_modal').modal('hide');
        block_screen('hide');
    }
});