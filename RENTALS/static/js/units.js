document.addEventListener('DOMContentLoaded', function() {
    const selectAllCheckbox = document.getElementById('selectAllCheckbox');
    const unitCheckboxes = document.querySelectorAll('.unit-checkbox');
    const deleteSelectedBtn = document.getElementById('deleteSelectedBtn');
    const assignButtons = document.querySelectorAll('.assignTenantBtn');
    const detachButtons = document.querySelectorAll('.detachTenantBtn');
    const assignTenantForm = document.getElementById('assignTenantForm');
    
    // ======================
    // ASSIGN TENANT FUNCTIONALITY
    // ======================
    assignButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const unitId = this.getAttribute('data-unit-id');
            const unitName = this.getAttribute('data-unit-name');
            
            // Set unit info in modal
            document.getElementById('assignUnitId').value = unitId;
            document.getElementById('assignUnitName').textContent = unitName;
            
            // Fetch available tenants
            fetch(`/units/assign/${unitId}/`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                const tenantSelect = document.getElementById('assignTenantSelect');
                tenantSelect.innerHTML = '<option value="">-- Select a Tenant --</option>';
                
                if (data.tenants && data.tenants.length > 0) {
                    data.tenants.forEach(tenant => {
                        const option = document.createElement('option');
                        option.value = tenant.id;
                        option.textContent = `${tenant.first_name} ${tenant.last_name}`;
                        tenantSelect.appendChild(option);
                    });
                } else {
                    const option = document.createElement('option');
                    option.textContent = 'No available tenants';
                    option.disabled = true;
                    tenantSelect.appendChild(option);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to load tenants');
            });
        });
    });
    
    // Handle assign form submission
    if (assignTenantForm) {
        assignTenantForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const unitId = document.getElementById('assignUnitId').value;
            const tenantId = document.getElementById('assignTenantSelect').value;
            
            if (!tenantId) {
                alert('Please select a tenant');
                return;
            }
            
            const formData = new FormData();
            formData.append('tenant_id', tenantId);
            formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
            
            fetch(`/units/assign/${unitId}/`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert(data.message);
                    location.reload();
                } else {
                    alert(data.message || 'Failed to assign tenant');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while assigning the tenant');
            });
        });
    }
    
    // ======================
    // DETACH TENANT FUNCTIONALITY
    // ======================
    detachButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const unitId = this.getAttribute('data-unit-id');
            const unitName = this.getAttribute('data-unit-name');
            
            if (confirm(`Are you sure you want to detach the tenant from ${unitName}?`)) {
                const formData = new FormData();
                formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
                
                fetch(`/units/detach/${unitId}/`, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert(data.message);
                        location.reload();
                    } else {
                        alert(data.message || 'Failed to detach tenant');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred while detaching the tenant');
                });
            }
        });
    });
    
    // ======================
    // DELETE UNITS FUNCTIONALITY
    // ======================
    
    // Select/Deselect all
    selectAllCheckbox.addEventListener('change', function() {
        unitCheckboxes.forEach(checkbox => {
            checkbox.checked = this.checked;
        });
        updateDeleteButton();
    });
    
    // Update delete button visibility
    unitCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateDeleteButton);
    });
    
    function updateDeleteButton() {
        const anySelected = Array.from(unitCheckboxes).some(cb => cb.checked);
        deleteSelectedBtn.style.display = anySelected ? 'inline-block' : 'none';
    }
    
    // Delete selected units
    deleteSelectedBtn.addEventListener('click', function() {
        const selectedIds = Array.from(unitCheckboxes)
            .filter(cb => cb.checked)
            .map(cb => cb.value);
        
        if (selectedIds.length === 0) {
            alert('Please select at least one unit to delete');
            return;
        }
        
        if (confirm(`Are you sure you want to delete ${selectedIds.length} unit/s? This action cannot be undone.`)) {
            const formData = new FormData();
            selectedIds.forEach(id => formData.append('unit_ids[]', id));
            
            fetch('{% url "units:delete_units" %}', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value || ''
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert(data.message);
                    location.reload();
                } else {
                    alert(data.message || 'Failed to delete units');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while deleting units');
            });
        }
    });
});
