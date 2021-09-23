import {jsonEditor} from "../../sb-admin/custom-assets/js/mjs/helpers.mjs";


$(document).ready(function () {
    let fields = $('#id-fields'),
        object = $('input#id-object'),
        editor = jsonEditor($('div#id-digest-div')[0], $('textarea#id-digest'), false);

    fields.focus();

    function update_editor() {
        let template = JSON.parse(JSON.stringify(digest_template)),
            user_typed = fields.val(),
            field_list = null,
            current_fields = null;

        field_list = $.map(user_typed.split('\n'), function( val, i ) {
            return $.map(val.split(','), function (_val, _i) {
                return {"name": $.trim(_val)};
            });
        }).filter(item => !['', undefined, null, false].includes(item.name));


        current_fields = template['Digest-Node-Name'].parameters.fields;

        template['Digest-Node-Name'].parameters.fields = $.merge(current_fields, field_list);
        template['Digest-Node-Name'].parameters.object = object.val() || "Account";
        editor.set(template);
    }

    fields.on('keyup change', function() {
        update_editor(fields, object);
    });

    object.on('keyup change', function () {
        update_editor(fields, object);
    });

    $('button.clipboard').click(function () {
        navigator.clipboard.writeText(JSON.stringify(editor.get()));
        fields.focus();
    });

    $('button.reset').click(function () {
        fields.val('').trigger('change');
        object.val('').trigger('change');
        fields.focus();
    });
});