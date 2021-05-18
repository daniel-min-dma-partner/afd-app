$(document).ready(function(evt) {
    $('#id_extract').change(function() {
        extract_chkbx_evtmgr($(this).get(0))
    });
});

function extract_chkbx_evtmgr(checkbox_dom_e) {
    if(checkbox_dom_e.checked) {
        $("#id_replacers").val('').trigger('change');
        $('#id_replacers_display').prop('readonly', true);
        $('.card-title').text("Tree Extractor");
        $('#id_replacers').attr('onclick', 'return false');
    } else {
        $('.card-title').text(default_title);
        $('#id_replacers_display').prop('readonly', false);
        $('#id_replacers').removeAttr('onclick')
    }
}