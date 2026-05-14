    // 5. Tenant Upload Validation Logic
    const uploadForm = document.getElementById('uploadTenantsForm');
    const validateBtn = document.getElementById('validateTenantsBtn');
    const uploadBtn = document.getElementById('uploadTenantsBtn');
    const validationDiv = document.getElementById('tenantUploadValidation');

    if (validateBtn && uploadForm) {
        validateBtn.disabled = false;
        validateBtn.addEventListener('click', function() {
            const fileInput = document.getElementById('tenantsFile');
            const file = fileInput.files[0];
            if (!file) {
                alert('Please select a file');
                return;
            }
            const validTypes = ['text/csv', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'];
            if (!validTypes.includes(file.type) && !file.name.endsWith('.csv') && !file.name.endsWith('.xlsx')) {
                alert('Please upload a CSV or XLSX file');
                return;
            }
            const formData = new FormData();
            formData.append('file', file);
            formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));
            formData.append('validate_only', '1');
            validationDiv.style.display = 'block';
            validationDiv.innerHTML = 'Validating...';
            uploadBtn.style.display = 'none';
            fetch('/tenants/upload/', {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    let html = `<div class="alert alert-info">Validation complete.<br>Valid rows: <b>${data.valid_rows}</b><br>Invalid rows: <b>${data.invalid_rows}</b></div>`;
                    if (data.errors && data.errors.length) {
                        html += '<ul class="list-group">';
                        data.errors.forEach(err => {
                            html += `<li class="list-group-item list-group-item-danger">${err}</li>`;
                        });
                        html += '</ul>';
                        uploadBtn.style.display = 'none';
                    } else if (data.valid_rows > 0) {
                        uploadBtn.style.display = 'inline-block';
                    } else {
                        uploadBtn.style.display = 'none';
                    }
                    validationDiv.innerHTML = html;
                } else {
                    validationDiv.innerHTML = `<div class="alert alert-danger">${data.message || 'Validation failed.'}</div>`;
                    uploadBtn.style.display = 'none';
                }
            })
            .catch(error => {
                validationDiv.innerHTML = '<div class="alert alert-danger">Error validating file.</div>';
                uploadBtn.style.display = 'none';
            });
        });
        // Upload handler
        uploadBtn.addEventListener('click', function(e) {
            e.preventDefault();
            if (uploadBtn.style.display === 'none') return;
            const fileInput = document.getElementById('tenantsFile');
            const file = fileInput.files[0];
            if (!file) {
                alert('Please select a file');
                return;
            }
            const validTypes = ['text/csv', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'];
            if (!validTypes.includes(file.type) && !file.name.endsWith('.csv') && !file.name.endsWith('.xlsx')) {
                alert('Please upload a CSV or XLSX file');
                return;
            }
            const formData = new FormData();
            formData.append('file', file);
            formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));
            fetch('/tenants/upload/', {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    let message = `Successfully uploaded ${data.count} tenants`;
                    if (data.errors && data.errors.length) {
                        message += '\n\nWarnings:\n' + data.errors.slice(0, 5).join('\n');
                    }
                    alert(message);
                    window.location.reload();
                } else {
                    let errorMsg = data.message || 'Failed to upload tenants';
                    if (data.errors && data.errors.length) {
                        errorMsg += '\n\n' + data.errors.slice(0, 5).join('\n');
                    }
                    alert(errorMsg);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while uploading tenants');
            });
        });
    }
document.addEventListener('DOMContentLoaded', function() {
    const selectAllBtn = document.getElementById('selectAllTenants');
    const deleteBtn = document.getElementById('deleteSelectedTenantsBtn');

    // 1. Correct way to get CSRF token in Django
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // 2. Multi-select logic
    if (selectAllBtn) {
        selectAllBtn.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('.tenant-checkbox');
            checkboxes.forEach(cb => cb.checked = this.checked);
            toggleDeleteButton();
        });
    }

    // 3. Individual checkbox logic (using delegation)
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('tenant-checkbox')) {
            const allCheckboxes = document.querySelectorAll('.tenant-checkbox');
            const checkedCheckboxes = document.querySelectorAll('.tenant-checkbox:checked');
            
            // Sync the "Select All" checkbox state
            if (selectAllBtn) {
                selectAllBtn.checked = allCheckboxes.length === checkedCheckboxes.length;
            }
            toggleDeleteButton();
        }
    });

    function toggleDeleteButton() {
        const count = document.querySelectorAll('.tenant-checkbox:checked').length;
        if (deleteBtn) {
            deleteBtn.style.display = count > 0 ? 'inline-block' : 'none';
        }
    }

    // 4. Attach unit from tenant row
    const attachUnitButtons = document.querySelectorAll('.attachUnitBtn');
    const attachUnitForm = document.getElementById('attachUnitForm');
    const attachTenantId = document.getElementById('attachTenantId');
    const attachTenantName = document.getElementById('attachTenantName');
    const attachUnitSelect = document.getElementById('attachUnitSelect');
    const attachUnitInfo = document.getElementById('attachUnitInfo');

    attachUnitButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const tenantId = this.dataset.tenantId;
            const tenantName = this.dataset.tenantName;

            if (!tenantId) return;

            attachTenantId.value = tenantId;
            attachTenantName.textContent = tenantName;
            attachUnitInfo.textContent = 'Loading available units...';
            attachUnitSelect.innerHTML = '<option value="">-- Select a Unit --</option>';
            attachUnitSelect.disabled = true;

            fetch(`/tenants/available-units/${tenantId}/`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.units && data.units.length > 0) {
                    data.units.forEach(unit => {
                        const option = document.createElement('option');
                        option.value = unit.id;
                        option.textContent = `${unit.name} (${unit.property__name || 'Property'})`;
                        attachUnitSelect.appendChild(option);
                    });
                    attachUnitInfo.textContent = `${data.units.length} available unit(s) found.`;
                    attachUnitSelect.disabled = false;
                } else {
                    attachUnitInfo.textContent = 'No available units found for this tenant.';
                }
            })
            .catch(error => {
                console.error('Error loading units:', error);
                attachUnitInfo.textContent = 'Unable to load units right now.';
            });
        });
    });

    if (attachUnitForm) {
        attachUnitForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const tenantId = attachTenantId.value;
            const unitId = attachUnitSelect.value;
            if (!tenantId || !unitId) {
                alert('Please select a unit to attach.');
                return;
            }

            const formData = new FormData();
            formData.append('tenant_id', tenantId);
            formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));

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
                    window.location.reload();
                } else {
                    alert(data.message || 'Failed to attach unit.');
                }
            })
            .catch(error => {
                console.error('Error assigning unit:', error);
                alert('An error occurred while attaching the unit.');
            });
        });
    }

    // 4. The Delete Fetch
    if (deleteBtn) {
        deleteBtn.addEventListener('click', function() {
            const selectedIds = Array.from(document.querySelectorAll('.tenant-checkbox:checked'))
                                     .map(cb => cb.value);

            if (!confirm(`Delete ${selectedIds.length} tenants?`)) return;

            const formData = new FormData();
            selectedIds.forEach(id => formData.append('tenant_ids[]', id));

            // USE THE ABSOLUTE PATH matching your urls.py
            fetch('/tenants/delete/', { 
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    window.location.reload();
                } else {
                    alert(data.message);
                }
            })
            .catch(err => alert("Communication error with server. Check URL configuration."));
        });
    }
});