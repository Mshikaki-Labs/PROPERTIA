// Flatpickr initialization for all date inputs with modern UI
// Requires flatpickr to be loaded globally

document.addEventListener('DOMContentLoaded', function() {
    if (window.flatpickr) {
        // Detect paired date-range inputs (start_date / end_date)
        const rangePairs = {};
        document.querySelectorAll('input.datepicker').forEach(function(input) {
            const name = input.getAttribute('name');
            const form = input.closest('form');
            if (form && (name === 'start_date' || name === 'startDate')) {
                const pair = form.querySelector('input.datepicker[name="end_date"], input.datepicker[name="endDate"]');
                if (pair) {
                    const key = form.id || Math.random();
                    rangePairs[key] = { start: input, end: pair, inited: false };
                }
            }
        });

        // Initialize paired date ranges with range mode
        Object.values(rangePairs).forEach(function(pair) {
            flatpickr(pair.start, {
                dateFormat: 'Y-m-d',
                allowInput: true,
                altInput: true,
                altFormat: 'M j, Y',
                appendTo: document.body,
                disableMobile: true,
                animate: true,
                monthSelectorType: 'dropdown',
                static: true,
                onChange: function(selectedDates) {
                    if (selectedDates.length > 0) {
                        pair.end._flatpickr.set('minDate', selectedDates[0]);
                    }
                },
            });
            flatpickr(pair.end, {
                dateFormat: 'Y-m-d',
                allowInput: true,
                altInput: true,
                altFormat: 'M j, Y',
                appendTo: document.body,
                disableMobile: true,
                animate: true,
                monthSelectorType: 'dropdown',
                static: true,
                onChange: function(selectedDates) {
                    if (selectedDates.length > 0) {
                        pair.start._flatpickr.set('maxDate', selectedDates[0]);
                    }
                },
            });
            pair.inited = true;
        });

        // Initialize standalone datepicker inputs (not part of a range)
        document.querySelectorAll('input.datepicker').forEach(function(input) {
            const name = input.getAttribute('name');
            if (name !== 'start_date' && name !== 'startDate' && name !== 'end_date' && name !== 'endDate') {
                flatpickr(input, {
                    dateFormat: 'Y-m-d',
                    allowInput: true,
                    altInput: true,
                    altFormat: 'M j, Y',
                    appendTo: document.body,
                    disableMobile: true,
                    animate: true,
                    monthSelectorType: 'dropdown',
                    static: true,
                });
            }
        });

        // Also initialize native date inputs that may not have been converted
        document.querySelectorAll('input[type="date"]:not(.flatpickr-input)').forEach(function(input) {
            if (!input.classList.contains('datepicker')) {
                input.classList.add('datepicker');
                flatpickr(input, {
                    dateFormat: 'Y-m-d',
                    allowInput: true,
                    altInput: true,
                    altFormat: 'M j, Y',
                    appendTo: document.body,
                    disableMobile: true,
                    animate: true,
                    monthSelectorType: 'dropdown',
                    static: true,
                });
            }
        });
    }
});
