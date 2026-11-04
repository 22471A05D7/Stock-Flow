/*
 * StockFlow - small client-side helpers.
 * Loaded on every page (see base.html / product_list.html).
 */
document.addEventListener('DOMContentLoaded', function () {

    /* 1. Delete confirmation modal: wire the clicked row's product
     *    name and delete URL into the shared modal form. */
    var deleteModal = document.getElementById('deleteModal');
    if (deleteModal) {
        deleteModal.addEventListener('show.bs.modal', function (event) {
            var button = event.relatedTarget;
            if (!button) { return; }
            var form = document.getElementById('deleteForm');
            form.action = button.getAttribute('data-url');
            var span = document.getElementById('deleteProductName');
            if (span) { span.textContent = button.getAttribute('data-name'); }
        });
    }

    /* 2. Auto-dismiss success/info notifications after 4 seconds. */
    document.querySelectorAll('.app-alert').forEach(function (el) {
        var isInfo = el.classList.contains('alert-success') ||
                     el.classList.contains('alert-info');
        if (isInfo) {
            setTimeout(function () {
                bootstrap.Alert.getOrCreateInstance(el).close();
            }, 4000);
        }
    });
});
