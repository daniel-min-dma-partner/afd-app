import {submit_with_screencover} from '../../sb-admin/custom-assets/js/mjs/helpers.mjs';

$('#id_file').on('change', (evt) => {
    selected_df_name = evt.target.files[0].name;
});

$("#submit-modal-trigger").on('click', (evt) => {
    let envname = $('#id_env_selector').select2('data')[0].text,
        dfname = selected_df_name;
    envname = envname === 'Select One' ? "" : '<code>' + envname + '</code>';
    dfname = [null, "", undefined].includes(dfname) ? "" : '<code>' + dfname + '</code>';

    $('.confirmation-context').html(`Upload the dataflow ${dfname} to the Salesforce Instance ${envname}.`);
    $('.modal-title').html("Are you sure to proceed with the following?");
});

$('#confirmation-proceed').on('click', (evt) => {
    let envname = $('#id_env_selector').select2('data')[0].text;
    submit_with_screencover($('#submit-btn'), $('#id_modal'), "Upload now?",
            `Uploading ${selected_df_name} to ${envname}`);
});