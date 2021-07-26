import {popup_notification} from "../../sb-admin/custom-assets/js/mjs/helpers.mjs";

$(".btn-copy-to-clip").click((evt) => {
    $("#id_saql").focus().select();
    document.execCommand("copy");

    if (($("#id_saql").val()).length > 0) {
        popup_notification("Copying to Clipboard", "Success", "success");
    }
});