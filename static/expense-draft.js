// Keeps the new expense form while the user visits another page and comes back.
// The draft lives in sessionStorage, so it belongs to this tab only.
(function () {
    const form = document.querySelector("form[data-draft]");

    if (!form) { return; }

    const key = form.dataset.draft;
    const fieldNames = ["name", "amount", "category_id", "date"];

    function readDraft() {
        try {
            return JSON.parse(sessionStorage.getItem(key)) || {};
        } catch (error) {
            return {};
        }
    }

    function saveDraft() {
        const draft = {};

        fieldNames.forEach(function (fieldName) {
            draft[fieldName] = form.elements[fieldName].value;
        });

        try {
            sessionStorage.setItem(key, JSON.stringify(draft));
        } catch (error) {
            // Storage can be blocked: the form still works, only without a draft
        }
    }

    function clearDraft() {
        try {
            sessionStorage.removeItem(key);
        } catch (error) {
            // Nothing to clear
        }
    }

    const draft = readDraft();

    fieldNames.forEach(function (fieldName) {
        if (draft[fieldName]) {
            form.elements[fieldName].value = draft[fieldName];
        }
    });

    // Show the category suggestion again, but only while no category has been chosen
    if (draft.name && !draft.category_id) {
        form.elements["name"].dispatchEvent(new Event("input"));
    }

    form.addEventListener("input", saveDraft);
    form.addEventListener("change", saveDraft);
    form.addEventListener("submit", clearDraft);

    form.querySelectorAll("[data-clear-draft]").forEach(function (element) {
        element.addEventListener("click", clearDraft);
    });
})();