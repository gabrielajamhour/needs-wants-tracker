(function () {
    var dialog = document.getElementById("emoji-dialog");
    if (!dialog || typeof dialog.showModal !== "function") {
        return; // no dialog support: the text fields keep working on their own
    }
    var picker = dialog.querySelector("emoji-picker");
    var fields = document.querySelectorAll(".emoji-field");
    var current = null;

    function enhance(field) {
        var input = field.querySelector(".emoji-input");
        var button = field.querySelector(".emoji-open");
        input.hidden = true; // stays in the form, but is no longer shown
        button.hidden = false;
        button.addEventListener("click", function () {
            current = { input: input, button: button };
            dialog.showModal();
        });
    }

    // Only replace the text fields once the picker component has really loaded
    customElements.whenDefined("emoji-picker").then(function () {
        fields.forEach(enhance);
    });

    picker.addEventListener("emoji-click", function (event) {
        if (current) {
            var emoji = event.detail.unicode;
            current.input.value = emoji;
            current.button.textContent = emoji;
            current.button.setAttribute("aria-label", "Change emoji, current: " + emoji);
        }
        dialog.close();
    });
})();