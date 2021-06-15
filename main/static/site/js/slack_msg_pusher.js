$("#"+has_manager_approval_field_id).on('change', function(evt) {
    enable_manager_name_field();
});

const enable_manager_name_field = () => {
    let is_checked = $("#"+has_manager_approval_field_id).get(0).checked;

    $("#"+manager_name_field_id).prop('readonly', !is_checked);
    $("#"+manager_name_field_id).val('').trigger('change');
};