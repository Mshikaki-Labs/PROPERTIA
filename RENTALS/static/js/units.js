document.addEventListener('DOMContentLoaded', function() {
    // ======================
    // UNIT UPLOAD LOGIC
    // ======================
    const uploadForm = document.getElementById('uploadUnitsForm');
    const validateBtn = document.getElementById('validateUnitsBtn');
    const uploadBtn = document.getElementById('uploadUnitsBtn');
    const validationDiv = document.getElementById('unitUploadValidation');

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

    function showValidationMessage(type, title, messages = []) {
        if (!validationDiv) return;
        const alertClass = type === 'success' ? 'alert-success' : type === 'info' ? 'alert-info' : 'alert-danger';
        const listHtml = messages.length
            ? `<ul class="mb-0 mt-2">${messages.map(message => `<li>${message}</li>`).join('')}</ul>`
            : '';
        validationDiv.className = `alert ${alertClass}`;
        validationDiv.innerHTML = `<div class="fw-semibold">${title}</div>${listHtml}`;
        validationDiv.style.display = 'block';
    }

    function resetUploadActions() {
        if (uploadBtn) {
            uploadBtn.style.display = 'none';
            uploadBtn.disabled = false;
            uploadBtn.textContent = 'Upload';
        }
        if (validateBtn) {
            validateBtn.style.display = 'inline-block';
            validateBtn.disabled = false;
            validateBtn.textContent = 'Validate';
        }
        if (validationDiv) {
            validationDiv.className = 'alert d-none';
            validationDiv.innerHTML = '';
        }
    }

    function getSelectedUnitFile() {
        const fileInput = document.getElementById('unitsFile');
        const file = fileInput && fileInput.files ? fileInput.files[0] : null;
        if (!file) {
            showValidationMessage('error', 'Please select a file');
            return null;
        }
        const validTypes = ['text/csv', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'];
        if (!validTypes.includes(file.type) && !file.name.endsWith('.csv') && !file.name.endsWith('.xlsx')) {
            showValidationMessage('error', 'Please upload a CSV or XLSX file');
            return null;
        }
        return file;
    }

    function postUnitUpload(validateOnly) {
        const file = getSelectedUnitFile();
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);
        formData.append('csrfmiddlewaretoken', uploadForm.querySelector('[name=csrfmiddlewaretoken]').value);
        if (validateOnly) {
            formData.append('validate_only', '1');
        }

        if (validateOnly && validateBtn) {
            validateBtn.disabled = true;
            validateBtn.textContent = 'Validating...';
        }
        if (!validateOnly && uploadBtn) {
            uploadBtn.disabled = true;
            uploadBtn.textContent = 'Uploading...';
        }

        fetch('/units/upload/', {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            const detailMessages = data.errors ? data.errors.slice(0, 10) : [];

            if (validateOnly) {
                if (data.success) {
                    showValidationMessage('success', data.message || `Validation complete: ${data.valid_rows || 0} valid, ${data.invalid_rows || 0} invalid.`, detailMessages);
                    if (uploadBtn) {
                        uploadBtn.style.display = 'inline-block';
                        uploadBtn.disabled = false;
                        uploadBtn.textContent = 'Upload';
                    }
                    if (validateBtn) validateBtn.style.display = 'none';
                } else {
                    showValidationMessage('error', data.message || 'Validation failed', detailMessages);
                    if (uploadBtn) uploadBtn.style.display = 'none';
                    if (validateBtn) {
                        validateBtn.disabled = false;
                        validateBtn.textContent = 'Validate';
                    }
                }
                return;
            }

            if (data.success) {
                showValidationMessage('success', data.message || `Successfully uploaded ${data.count} units`, detailMessages);
                setTimeout(function() {
                    window.location.reload();
                }, 1500);
            } else {
                showValidationMessage('error', data.message || 'Failed to upload units', detailMessages);
                if (uploadBtn) {
                    uploadBtn.disabled = false;
                    uploadBtn.textContent = 'Upload';
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showValidationMessage('error', validateOnly ? 'An error occurred while validating units' : 'An error occurred while uploading units');
            if (validateBtn) {
                validateBtn.disabled = false;
                validateBtn.textContent = 'Validate';
            }
            if (uploadBtn) {
                uploadBtn.disabled = false;
                uploadBtn.textContent = 'Upload';
            }
        });
    }

    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            postUnitUpload(true);
        });

        if (uploadBtn) {
            uploadBtn.addEventListener('click', function() {
                postUnitUpload(false);
            });
        }

        const uploadModal = document.getElementById('uploadUnitsModal');
        if (uploadModal) {
            uploadModal.addEventListener('hidden.bs.modal', function() {
                uploadForm.reset();
                resetUploadActions();
            });
        }
    }

    const unitsPage = document.getElementById('unitsPage');
    const deleteUnitsUrl = unitsPage ? unitsPage.dataset.deleteUrl : '/units/delete/';
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
            if (!window.downloadSelectedRowsBeforeDelete('.unit-checkbox:checked', 'units-before-delete')) return;

            const formData = new FormData();
            selectedIds.forEach(id => formData.append('unit_ids[]', id));
            
            fetch(deleteUnitsUrl, {
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
