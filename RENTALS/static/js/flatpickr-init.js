// Flatpickr initialization for all date inputs
// Requires flatpickr to be loaded globally

document.addEventListener('DOMContentLoaded', function() {
    if (window.flatpickr) {
        document.querySelectorAll('input[type="date"], input.datepicker').forEach(function(input) {
            flatpickr(input, {
                dateFormat: 'Y-m-d',
                allowInput: true,
                altInput: true,
                altFormat: 'F j, Y',
                appendTo: document.body,
                disableMobile: true,
            });
        });
    }
});
