import {jsonEditor} from "../../sb-admin/custom-assets/js/mjs/helpers.mjs";


$(document).ready(function () {
    let fields = $('#id-fields'),
        object = $('input#id-object'),
        editor = jsonEditor($('div#id-digest-div')[0], $('textarea#id-digest'), false),
        dataset = $('#id-dataset');

    fields.focus();

    function update_editor() {
        let template = JSON.parse(JSON.stringify(digest_template)),
            user_typed = fields.val(),
            user_dataset = dataset.val(),
            field_list = null,
            current_fields = null,
            current_dataset = null,
            current_ds_alias = null;

        field_list = $.map(user_typed.split('\n'), function( val, i ) {
            return $.map(val.split(','), function (_val, _i) {
                return {"name": $.trim(_val)};
            });
        })
            .filter(item => !['', undefined, null, false].includes(item.name))
            .sort(function(a, b){
                return a.name.localeCompare(b.name);
            });


        current_fields = template['Digest-Node-Name'].parameters.fields;
        current_dataset = template['Register-Dataset'].parameters.name;
        current_ds_alias = template['Register-Dataset'].parameters.alias;


        template['Digest-Node-Name'].parameters.fields = field_list.length ? field_list : current_fields;
        template['Digest-Node-Name'].parameters.object = object.val() || "Account";
        template['Register-Dataset'].parameters.name = user_dataset.replace(/ +/g, ' ') || current_dataset;
        template['Register-Dataset'].parameters.alias = user_dataset.replace(/ +/g, '_') || current_ds_alias;
        editor.set(template);
    }

    fields.on('keyup change', function() {
        update_editor(fields, object);
    });

    object.on('keyup change', function () {
        update_editor(fields, object);
    });

    dataset.on('keyup change', function () {
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