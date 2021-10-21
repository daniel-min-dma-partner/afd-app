$(document).ready(function (evt) {
    let dataTable = $("#dataTable").DataTable({
        "lengthMenu": [[10, 25, 50, -1], [10, 25, 50, "All"]],
        "order": [[ 0, "desc" ]],
    });
    // #myInput is a <input type="text"> element
    $('input[type="search"]').on('keyup', function () {
        dataTable.search( this.value.trim() ).draw();
    });
});