$(document).ready(function(evt) {
    extract_chkbx_evtmgr($('#id_extract').get(0));

    $('#id_extract').change(function() {
        extract_chkbx_evtmgr($(this).get(0));
    });
});

function extract_chkbx_evtmgr(checkbox_dom_e) {
    if(checkbox_dom_e.checked) {
        $("#id_replacers").val('').trigger('change');
        $('#id_replacers').prop('readonly', true);
        $('#id_replacers').attr('onclick', 'return false');
        $('#id_name').prop('readonly', false);
    } else {
        $('#id_replacers').prop('readonly', false);
        $('#id_replacers').removeAttr('onclick');
        $('#id_name').val('').trigger('change');
        $('#id_name').prop('readonly', true);
    }
}