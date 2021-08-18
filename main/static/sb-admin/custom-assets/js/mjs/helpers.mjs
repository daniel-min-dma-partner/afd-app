const build_toast = () => {
    // // Bootstrap Toast construction - Bootstrap 5.0.2
    // let toastElList = [].slice.call(document.querySelectorAll('.toast'));
    // let toastList = toastElList.map(function (toastEl) {
    //     return new bootstrap.Toast(toastEl, {autohide: false});
    // });
    //
    // // Shows Toasts
    // $.each(toastList, function (index, element) {
    //     element.show();
    // });

    // Boostrap Toast Construction - Bootstrap 4.6.0
    $('.toast').toast('show');

    // Closes the notification box when "x" is clicked
    $('.btn-close').click(function (evt) {
        $(this).parent().parent().toast('hide');
    });

    // Closes the toast when header or body is clicked
    $('.toast-header, .toast-body').click(function (evt) {
        $(this).parent().toast('hide');
    });
};

const popup_notification = (title = "Default Title", content = "Default Content", type = "success", autohide = false, delay = null) => {
    // Deletes DOM element if exists
    let toastdiv = $('div.my-toast');
    if (toastdiv.length !== 0) {
        toastdiv.remove();
    }

    // Html template for Notifications
    let toast_template = "<div aria-live=\"polite\" aria-atomic=\"true\" class=\"my-toast\">\n" +
        "    <div class=\"toast-container position-absolute top-0 end-0 p-3\">\n" +
        "        <div class=\"toast\" role=\"alert\" aria-live=\"assertive\" aria-atomic=\"true\"" + (autohide === false ? ' data-autohide="false"' : "") + (delay === null ? "" : ' data-delay=' + delay) + ">\n" +
        "            <div class=\"toast-header bg-" + type + "\">\n" +
        "                <strong class=\"me-auto\">" + title + "</strong>\n" +
        "                <small class=\"text-muted\">just now</small>\n" +
        "                <button type=\"button\" class=\"btn-close\" data-bs-dismiss=\"toast\"\n" +
        "                        aria-label=\"Close\"></button>\n" +
        "            </div>\n" +
        "            <div class=\"toast-body\">\n" +
        "               " + content + "\n" +
        "            </div>\n" +
        "        </div>\n" +
        "    </div>\n" +
        "</div>";

    // Test inserting forcefully toast
    $('body').find('.container-fluid').prepend(toast_template);

    // Build toast
    build_toast();
};

const show_error_and_popup = (response) => {
    if (response.responseJSON !== null && response.responseJSON !== undefined) {
        if ('error' in response.responseJSON) {
            popup_notification("Warning", response.responseJSON['error'], 'warning');
        } else {
            popup_notification("Warning", JSON.stringify(response.responseJSON), 'warning');
        }
    } else {
        if (!(response.statusText in [null, '', undefined]) && response.statusText === 'abort') {
            return false;
        }
        popup_notification("Warning", response.statusText, 'warning');
    }
};

const block_screen = (mode='show') => {
  $('.screen-blocker').modal(mode);
};

export {build_toast, popup_notification, show_error_and_popup, block_screen};