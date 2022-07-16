$(document).ready(function (evt) {
    $('#id_name').focus();

    const env_radiobutton_onchange = () => {
        let custom_env_rbutton = $("#id_environment_2"),
            custom_domain_textfield = $('#id_custom_domain');
        if (custom_env_rbutton[0].checked) {
            if (custom_domain_textfield.parent().hasClass('d-none')) custom_domain_textfield.parent().removeClass('d-none');
        } else {
            if (!custom_domain_textfield.parent().hasClass('d-none')) custom_domain_textfield.parent().addClass('d-none');
            custom_domain_textfield.val('').trigger('change');
        }
    };

    $('input[id^="id_environment"]').on('change', function (evt) {
        env_radiobutton_onchange();
    });
});