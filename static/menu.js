(function () {
    var menu = document.querySelector(".menu");
    if (!menu) {
        return;
    }

    // Close the menu when clicking anywhere outside it
    document.addEventListener("click", function (event) {
        if (!menu.contains(event.target)) {
            menu.open = false;
        }
    });

    // Close the menu with Escape and return focus to its button
    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && menu.open) {
            menu.open = false;
            menu.querySelector("summary").focus();
        }
    });
})();