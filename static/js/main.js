// Datepicker initialization from equipment_list.html moved to here for modularity
// Note: You need jQuery for bootstrap-datepicker, or use a pure JS alternative like Flatpickr.
// For simplicity, I'm assuming jQuery is available or you add it.
// If not, replace with a pure JS datepicker.

// If you want to keep the snippet in base.html's script block, remove this.
// Otherwise, ensure jQuery is loaded BEFORE this script if using bootstrap-datepicker.

document.addEventListener('DOMContentLoaded', function() {
    // Initialize datepicker if elements exist
    if (typeof jQuery !== 'undefined' && $.fn.datepicker) {
        $('.datepicker').datepicker({
            format: 'yyyy-mm-dd',
            language: 'ru',
            autoclose: true,
            todayHighlight: true
        });
    }

    // Handle delete modal dynamically for equipment_list.html
    var deleteModal = document.getElementById('deleteModal');
    if (deleteModal) {
        deleteModal.addEventListener('show.bs.modal', function (event) {
            var button = event.relatedTarget;
            var assetId = button.getAttribute('data-asset-id');
            var assetName = button.getAttribute('data-asset-name');
            
            var modalAssetName = deleteModal.querySelector('#modalAssetName');
            var deleteForm = deleteModal.querySelector('#deleteForm');

            if (modalAssetName) modalAssetName.textContent = assetName;
            if (deleteForm) {
                // Ensure url_for is replaced dynamically with correct Flask URL.
                // In a real app, you'd pass a base URL or template the full URL.
                // For simplicity here, we'll assume the URL structure.
                deleteForm.action = `/equipment/delete/${assetId}`;
            }
        });
    }
});
