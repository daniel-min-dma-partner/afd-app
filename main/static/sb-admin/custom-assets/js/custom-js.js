$(document).ready(function(evt) {
    var toastElList = [].slice.call(document.querySelectorAll('.toast'));
    var toastList = toastElList.map(function (toastEl) {
        return new bootstrap.Toast(toastEl);
    });

    $.each(toastList, function(index, element) {
        element.show();
    });

    $('select').select2();
});

$('.logout').click(function() {
    $('#logoutModal .modal-footer').find('a.btn-primary').attr('href', $(this).data('action'));
    $('#logoutModal .modal-body').html("You'll be log-ed out.");
});

$('.btn-close').click(function(evt) {
    $(this).parent().parent().hide();
});