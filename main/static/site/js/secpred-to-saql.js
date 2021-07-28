import {popup_notification} from "../../sb-admin/custom-assets/js/mjs/helpers.mjs";

$('#id_secpred').keyup(function (e) {
    generate_saql($(this), $("#id_saql"), $("#id_dataset"));
    generate_saql2($(this), $("#id_saql2"));
});

$('#id_dataset').keyup(function (e) {
    generate_saql($("#id_secpred"), $("#id_saql"), $($(this)));
});

const generate_saql = (secpred_field, saql_field, dataset_field) => {
    let value = secpred_field.val(),
        tokens = value.split("||").map((element) => {
            let regex = /'[A-Za-z_0-9-']+/g;
            return regex.exec(element.trim());
        }).map((element) => {
            return element === null ? "" : element[0].replaceAll("'", '')
        }),
        dataset = dataset_field.val(),
        saql = tokens.join("") === "" ? "" : "q = load \"" + dataset + "\";\n" +
            "q = foreach q generate '" + tokens.join("', '") + "';\n" +
            "q = limit q 10;"
    ;

    saql_field.val(saql).trigger('change');
};

const generate_saql2 = (secpred_field, saql_field) => {
    let value = secpred_field.val(),
        saql = value.replace(/\s\s+/g, ' ')
            .replaceAll('‘', "'")
            .replaceAll('’', "'")
            .replaceAll('“', '"')
            .replaceAll('”', '"')
            .replaceAll('"||', '" ||')
            .replaceAll('||"', '|| "')
            .replaceAll("'||", "' ||")
            .replaceAll("||'", "|| '")
            .replaceAll("'==", "' ==")
            .replaceAll("=='", "== '")
            .replaceAll('"==', '" ==')
            .replaceAll('=="', '== "')
            .replaceAll('\"==', '\" ==')
            .replaceAll('==\"', '== \"')
            .replace(/\s\s+/g, ' ')
    ;

    saql_field.val(saql).trigger('change');
};

$(".btn-copy-to-clip").click((evt) => {
    $("#id_saql").focus().select();
    document.execCommand("copy");

    if (($("#id_saql").val()).length > 0) {
        popup_notification("Copying to Clipboard", "Success", "success");
    }
});

$(".btn-copy-to-clip2").click((evt) => {
    $("#id_saql2").focus().select();
    document.execCommand("copy");

    if (($("#id_saql").val()).length > 0) {
        popup_notification("Copying to Clipboard", "Success", "success");
    }
});