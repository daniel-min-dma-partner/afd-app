import {jsonEditor} from '../../sb-admin/custom-assets/js/mjs/helpers.mjs';

$(document).ready(function (evt) {
    jsonEditor($('#json-holder')[0], $('#id_dataflow'));
});

$("#btn-submit").on('click', function (evt) {
    if (confirm("Are you sure?")) {
        $('button[type="submit"]').click();
    }
});