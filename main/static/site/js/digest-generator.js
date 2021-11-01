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
            field_lists,
            current_dataset,
            current_ds_alias,
            objects, _object,
            fieldlist;

        field_lists = user_typed.split('--').filter(item => !['', undefined, null, false, []].includes(item)).map(function (fieldlist, i) {
            return fieldlist.split('\n').filter(item => !['', undefined, null, false].includes(item)).map(function (field, i) {
                return {"name": $.trim(field)};
            });
        }).filter(item => !['', undefined, null, false, []].includes(item));

        objects = object.val().split(',').filter(item => !['', undefined, null, false].includes(item)).map(function (dataset, i) {
            return dataset.trim();
        });

        for (let i = 0; i < objects.length; i++) {
            if (i < field_lists.length) {

                fieldlist = field_lists[i];

                if (fieldlist.length) {
                    current_dataset = template['Register-Dataset'].parameters.name;
                    current_ds_alias = template['Register-Dataset'].parameters.alias;
                    _object = objects[i];

                    template[_object] = JSON.parse(JSON.stringify(template['Digest-Node-Name']));
                    template[_object].parameters.fields = field_lists[i];
                    template[_object].parameters.object = _object;
                    template['Register-Dataset'].parameters.name = user_dataset.replace(/ +/g, ' ') || current_dataset;
                    template['Register-Dataset'].parameters.alias = user_dataset.replace(/ +/g, '_') || current_ds_alias;
                }
            }
        }

        if (Object.keys(template).length > 2) {
            delete template['Digest-Node-Name'];
            template['Register-Dataset'].parameters.source = "<< specify here the last node >>";
        }

        editor.set(template);
    }

    fields.on('keyup change', function () {
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