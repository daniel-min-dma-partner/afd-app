$('.logout').click(function() {
    $('#logoutModal .modal-footer').find('a.btn-primary').attr('href', $(this).data('action'));
    $('#logoutModal .modal-body').html("You'll be log-ed out.");
});