// Delete asks for confirmation in the app's own dialog. Without dialog support, the
// browser's confirm() set on each form in the template keeps working.
(function () {
    var dialog = document.getElementById("delete-dialog");
    if (!dialog || typeof dialog.showModal !== "function") {
        return;
    }

    var form = document.getElementById("delete-form");
    var name = document.getElementById("delete-name");
    var amount = document.getElementById("delete-amount");
    var cancel = document.getElementById("delete-cancel");

    document.querySelectorAll("form[data-delete-name]").forEach(function (rowForm) {
        rowForm.removeAttribute("onsubmit"); // The dialog replaces confirm()
        rowForm.addEventListener("submit", function (event) {
            event.preventDefault();
            form.action = rowForm.action;
            name.textContent = rowForm.dataset.deleteName;
            amount.textContent = rowForm.dataset.deleteAmount;
            dialog.showModal();
        });
    });

    cancel.addEventListener("click", function () {
        dialog.close();
    });

    // A click on the dimmed backdrop closes the dialog too
    dialog.addEventListener("click", function (event) {
        if (event.target === dialog) {
            dialog.close();
        }
    });
})();