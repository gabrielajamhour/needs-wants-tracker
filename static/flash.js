// Success and info messages fade out by themselves; errors stay until they are closed.
(function () {
    var DELAY = 3000;
    var FADE = 300;

    function dismiss(flash) {
        flash.classList.add("is-leaving");
        setTimeout(function () {
            flash.remove();
        }, FADE);
    }

    document.querySelectorAll(".flash").forEach(function (flash) {
        var close = flash.querySelector(".flash-close");
        if (close) {
            close.hidden = false;
            close.addEventListener("click", function () {
                dismiss(flash);
            });
        }

        if (!flash.classList.contains("error")) {
            setTimeout(function () {
                dismiss(flash);
            }, DELAY);
        }
    });
})();