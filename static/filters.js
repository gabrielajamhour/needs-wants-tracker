// Filters apply as soon as they change: the selects at once,
// the search after a short pause or when Enter is pressed.
(function () {
    var form = document.querySelector(".filter-bar");
    if (!form) {
        return;
    }

    var SEARCH_DELAY = 400;
    var FOCUS_KEY = "focus-search";
    var search = form.elements.q;
    var timer = null;

    function apply() {
        clearTimeout(timer);
        form.submit();
    }

    var category = form.elements.category_id;
    var type = form.elements.type;

    // Choosing a category fills in its type
    category.addEventListener("change", function () {
        var option = category.selectedOptions[0];
        if (option && option.dataset.type) {
            type.value = option.dataset.type;
        }
    });

    // Choosing a type that does not match the chosen category clears the category
    type.forEach(function (radio) {
        radio.addEventListener("change", function () {
            var option = category.selectedOptions[0];
            if (type.value && option && option.dataset.type && option.dataset.type !== type.value) {
                category.value = "";
            }
        });
    });

    form.querySelectorAll("select, input[type=radio]").forEach(function (control) {
        control.addEventListener("change", apply);
    });

    search.addEventListener("input", function () {
        clearTimeout(timer);
        timer = setTimeout(function () {
            // The page reloads, so remember to put the cursor back in the search field
            try {
                sessionStorage.setItem(FOCUS_KEY, "1");
            } catch (error) {
                // Storage can be blocked; the filter still works without the cursor
            }
            apply();
        }, SEARCH_DELAY);
    });

    // Enter sends the form on its own; stop the pending delay so it is sent once
    form.addEventListener("submit", function () {
        clearTimeout(timer);
    });

    // After a reload caused by typing, keep typing where the user left off
    try {
        if (sessionStorage.getItem(FOCUS_KEY)) {
            sessionStorage.removeItem(FOCUS_KEY);
            search.focus();
            search.setSelectionRange(search.value.length, search.value.length);
        }
    } catch (error) {
        // Nothing to restore
    }
})();