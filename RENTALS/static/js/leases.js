document.addEventListener('DOMContentLoaded', function() {
    const propertyFilter = document.getElementById('leasePropertyFilter');
    const unitFilter = document.getElementById('leaseUnitFilter');

    if (!propertyFilter || !unitFilter) {
        return;
    }

    function setUnitOptions(units) {
        unitFilter.innerHTML = '';

        const allUnitsOption = document.createElement('option');
        allUnitsOption.value = '';
        allUnitsOption.textContent = 'All Units';
        unitFilter.appendChild(allUnitsOption);

        units.forEach(function(unit) {
            const option = document.createElement('option');
            option.value = unit.id;
            option.textContent = `${unit.name} (${unit.property})`;
            unitFilter.appendChild(option);
        });
    }

    function loadUnitsForProperty(propertyId) {
        const unitsUrl = unitFilter.dataset.unitsUrl || '/leases/units/';
        const url = propertyId ? `${unitsUrl}?property=${encodeURIComponent(propertyId)}` : unitsUrl;

        unitFilter.disabled = true;
        fetch(url, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
            .then(function(response) {
                if (!response.ok) {
                    throw new Error('Unable to load units');
                }
                return response.json();
            })
            .then(function(data) {
                setUnitOptions(data.units || []);
            })
            .catch(function() {
                setUnitOptions([]);
            })
            .finally(function() {
                unitFilter.disabled = false;
            });
    }

    propertyFilter.addEventListener('change', function() {
        unitFilter.value = '';
        loadUnitsForProperty(this.value);
    });
});
