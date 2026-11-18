// Changing the month on the expense list keeps the filters as they are on screen,
// even ones the user picked without pressing "Filter" yet.
(function () {
    var filters = document.querySelector(".filter-bar");
    var nav = document.querySelector(".month-nav");
    if (!filters || !nav) {
        return;
    }

    var NAMES = ["category_id", "type", "q"];

    function currentFilters() {
        var values = {};
        NAMES.forEach(function (name) {
            var field = filters.elements[name];
            var value = field ? field.value.trim() : "";
            if (value) {
                values[name] = value;
            }
        });
        return values;
    }

    // Arrows: rebuild the link with the filters shown on screen
    nav.querySelectorAll("a[href]").forEach(function (link) {
        link.addEventListener("click", function () {
            var url = new URL(link.href, window.location.href);
            var values = currentFilters();
            NAMES.forEach(function (name) {
                if (values[name]) {
                    url.searchParams.set(name, values[name]);
                } else {
                    url.searchParams.delete(name);
                }
            });
            link.href = url.toString();
        });
    });

    // Picker: replace its hidden fields right before the form is sent
    var picker = nav.querySelector(".month-picker");
    if (picker) {
        picker.addEventListener("formdata", function (event) {
            var values = currentFilters();
            NAMES.forEach(function (name) {
                event.formData.delete(name);
                if (values[name]) {
                    event.formData.set(name, values[name]);
                }
            });
        });
    }
})();
