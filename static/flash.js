(function () {
    var AUTO_HIDE_MS = 3000;

    function dismiss(flash) {
        if (flash.classList.contains("is-leaving")) {
            return;
        }
        flash.classList.add("is-leaving");
        setTimeout(function () { flash.remove(); }, 300);
    }

    document.querySelectorAll(".flash").forEach(function (flash) {
        flash.querySelector(".flash-close").addEventListener("click", function () {
            dismiss(flash);
        });

        // Errors stay until dismissed: people need time to read them and fix the problem
        if (flash.dataset.flash === "error") {
            return;
        }

        var timer = setTimeout(function () { dismiss(flash); }, AUTO_HIDE_MS);

        function pause() { clearTimeout(timer); }
        function resume() { timer = setTimeout(function () { dismiss(flash); }, AUTO_HIDE_MS); }

        // Do not hide the message while it is hovered or focused
        flash.addEventListener("mouseenter", pause);
        flash.addEventListener("mouseleave", resume);
        flash.addEventListener("focusin", pause);
        flash.addEventListener("focusout", resume);
    });
})();