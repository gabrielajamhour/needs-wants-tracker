(function () {
    var form = document.querySelector(".month-picker");
    if (!form) {
        return;
    }
    var input = form.querySelector(".month-input");
    var button = form.querySelector(".month-calendar");

    // Browsers without a native month picker keep the plain field
    if (input.type !== "month") {
        return;
    }

    var initialValue = input.value;
    form.classList.add("is-enhanced");
    input.tabIndex = -1;
    button.hidden = false;

    button.addEventListener("click", function () {
        if (typeof input.showPicker === "function") {
            input.showPicker();
        } else {
            input.focus();
            input.click();
        }
    });

    // Reload only when a different month is chosen
    input.addEventListener("change", function () {
        if (input.value && input.value !== initialValue) {
            form.submit();
        }
    });
})();