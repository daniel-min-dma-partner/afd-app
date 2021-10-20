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
    let timeago = document.querySelector('time.timeago');
    if (timeago !== null) {
        document.querySelector('time.timeago').setAttribute('datetime', new Date().toISOString());
    }

    // Closes the notification box when "x" is clicked
    $('.btn-close').click(function (evt) {
        $(this).parent().parent().toast('hide');
    });

    // Closes the toast when header or body is clicked
    $('.toast-header, .toast-body').click(function (evt) {
        $(this).parent().toast('hide');
    });
};

const toast_remove = (toast_div = null) => {
    let toastdiv = toast_div || $('div.my-toast');
    if (toastdiv.length !== 0) {
        toastdiv.remove();
    }
};

const popup_notification = (title = "Default Title", content = "Default Content", type = "success", autohide = false, delay = null) => {
    // Deletes DOM element if exists
    let toastdiv = $('div.my-toast');
    if (toastdiv.length !== 0) {
        toastdiv.remove();
    }

    // Html template for Notifications
    let toast_template = "<div aria-live=\"polite\" aria-atomic=\"true\" class=\"my-toast\">\n" +
        "    <div class=\"toast-container position-fixed top-0 end-0 p-3\">\n" +
        "        <div class=\"toast\" role=\"alert\" aria-live=\"assertive\" aria-atomic=\"true\"" + (autohide === false ? ' data-autohide="false"' : "") + (delay === null ? "" : ' data-delay=' + delay) + ">\n" +
        "            <div class=\"toast-header bg-" + type + "\">\n" +
        "                <strong class=\"me-auto\">" + title + "</strong>\n" +
        "                <small class=\"text-muted\"><time class=\"timeago\" datetime=\"\">less than a minute ago</time></small>\n" +
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
    $('body').find('.toast-container').prepend(toast_template);

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

const submit_with_screencover = (submit_button, modal = null, confirm_msg = "Proceed?", progress_descriptor = "Progressing...") => {
    if ([undefined, "", null].includes(confirm_msg) || confirm(confirm_msg)) {
        modal ? modal.modal('hide') : null;
        show_screenplay(100, progress_descriptor);
        submit_button.click();
    } else {
        modal ? modal.modal('hide') : null;
        show_screenplay(0, progress_descriptor);
    }
};

const show_screenplay = (perc = 100, msg = "") => {
    document.getElementById("myNav").style.width = `${perc}%`;
    $('.progress-description').html(msg);
};


const alert_if_required_missing = () => {
    let required_fields_completed = true;

    $('input,textarea,select').filter('[required]').each(function (idx, element) {
        if ([null, undefined, ""].includes(element.value)) {
            popup_notification("Form Error", "Please complete all required fields (marked with <code><strong>*</strong></code>)", 'warning', true, 3000);
            required_fields_completed = false;
            return false;
        }
    });

    return required_fields_completed;
};

const jsonEditor = (container, json_field, mainMenuBar = true, modes = ['code', 'tree']) => {
    if (container) {
        // UI options.
        let options = {
            mainMenuBar: mainMenuBar,
            modes: modes,
            search: false,
        };

        // Converts strings to HTML tag.
        let json = JSON.parse($.trim(json_field.html()));

        // Set data.
        let editor = new JSONEditor(container, options);
        editor.set(json);

        // Event setup.
        editor.options.onModeChange = function (endMode, oldMode) {
            if (['tree', 'code'].includes(endMode)) {
                editor.expandAll();
            }
        };
        editor.options.onChange = function (evt) {
            try {
                let json = editor.get();
                json_field[0].value = $.trim(JSON.stringify(json));
                console.log(json_field[0].value);
            } catch (error) {
                return false;
            }
        };

        return editor;
    }

    return false;
};

export {
    build_toast, popup_notification, show_error_and_popup, submit_with_screencover, show_screenplay,
    alert_if_required_missing, jsonEditor, toast_remove
};