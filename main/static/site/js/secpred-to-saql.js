$('#id_secpred').keyup(function (e) {
    generate_saql($(this), $("#id_saql"), $("#id_dataset"));
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
            return element[0].replaceAll("'", '')
        }),
        dataset = dataset_field.val(),
        saql = "q = load '" + dataset + "';\n" +
            "q = foreach q generate '" + tokens.join("', '") + "';\n" +
            "q = limit q 10;"
    ;

    saql_field.val(saql).trigger('change');
};