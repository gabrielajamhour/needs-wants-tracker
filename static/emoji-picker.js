(function () {
    var dialog = document.getElementById("emoji-dialog");
    if (!dialog || typeof dialog.showModal !== "function") {
        return; // no dialog support: the text field keeps working on its own
    }
    var picker = dialog.querySelector("emoji-picker");
    var buttons = document.querySelectorAll(".emoji-open");
    var targetInput = null;

    // Show the buttons only once the picker component has actually loaded
    customElements.whenDefined("emoji-picker").then(function () {
        buttons.forEach(function (button) { button.hidden = false; });
    });

    buttons.forEach(function (button) {
        button.addEventListener("click", function () {
            targetInput = document.getElementById(button.dataset.for);
            dialog.showModal();
        });
    });

    picker.addEventListener("emoji-click", function (event) {
        if (targetInput) {
            targetInput.value = event.detail.unicode;
        }
        dialog.close();
    });
})();