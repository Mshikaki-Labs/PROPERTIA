document.addEventListener('DOMContentLoaded', function() {
    // ======================
    // TENANT UPLOAD LOGIC
    // ======================
    const uploadForm = document.getElementById('uploadTenantsForm');
    const validateBtn = document.getElementById('validateTenantsBtn');
    const uploadBtn = document.getElementById('uploadTenantsBtn');
    const validationDiv = document.getElementById('tenantUploadValidation');

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

    function getSelectedTenantFile() {
        const fileInput = document.getElementById('tenantsFile');
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

    function postTenantUpload(validateOnly) {
        const file = getSelectedTenantFile();
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

        fetch('/tenants/upload/', {
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
                showValidationMessage('success', data.message || `Successfully uploaded ${data.count} tenants`, detailMessages);
                setTimeout(function() {
                    window.location.reload();
                }, 1500);
            } else {
                showValidationMessage('error', data.message || 'Failed to upload tenants', detailMessages);
                if (uploadBtn) {
                    uploadBtn.disabled = false;
                    uploadBtn.textContent = 'Upload';
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showValidationMessage('error', validateOnly ? 'An error occurred while validating tenants' : 'An error occurred while uploading tenants');
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
            postTenantUpload(true);
        });

        if (uploadBtn) {
            uploadBtn.addEventListener('click', function() {
                postTenantUpload(false);
            });
        }

        const uploadModal = document.getElementById('uploadTenantsModal');
        if (uploadModal) {
            uploadModal.addEventListener('hidden.bs.modal', function() {
                uploadForm.reset();
                resetUploadActions();
            });
        }
    }

    // ======================
    // MULTI-SELECT LOGIC
    // ======================
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

            if (!selectedIds.length) return;
            if (!confirm(`Delete ${selectedIds.length} tenants?`)) return;
            if (!window.downloadSelectedRowsBeforeDelete('.tenant-checkbox:checked', 'tenants-before-delete')) return;

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
