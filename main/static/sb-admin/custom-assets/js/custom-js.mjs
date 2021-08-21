import {build_toast, show_screenplay} from './mjs/helpers.mjs';

$(document).ready(function (evt) {
    // Shows toasts if exists
    build_toast();

    // Applies Bootstrap Select2 Look & Feel for all select input
    // $('select').select2();
});

$('.logout').click(function () {
    $('#logoutModal .modal-footer').find('a.btn-primary').attr('href', $(this).data('action'));
    $('#logoutModal .modal-body').html("You'll be log-ed out.");
});

$('.menu-item-finder').on('keyup click', function(evt) {
    var processed_parent = [];

    $.each($('.collapse-item'), function (index, element) {
        let e = $(element),
            search_trm = $('.menu-item-finder').val().toLowerCase(),
            element_name = e.html().toLowerCase(),
            parent = e.parent().parent().parent(),
            parent_name = parent.find('span').html().toLowerCase(),
            search_matches = element_name.includes(search_trm) || parent_name.includes(search_trm),
            parent_processed = processed_parent.includes(parent_name);

        if ( !search_matches) {
            e.hide();
            if (!parent_processed) {
                parent.hide();
            }
        } else if (search_matches) {
            e.show();
            parent.show();
            processed_parent.push(parent_name);
        }
    });
});

$('.close-screenplay').on('click', (evt) => {
    show_screenplay(0);
});