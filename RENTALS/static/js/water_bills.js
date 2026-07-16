document.addEventListener('DOMContentLoaded', function() {
    const selectAllWaterBills = document.getElementById('selectAllWaterBills');
    const deleteSelectedWaterBillsBtn = document.getElementById('deleteSelectedWaterBillsBtn');
    const selectAllWaterBillPayments = document.getElementById('selectAllWaterBillPayments');
    const deleteSelectedWaterBillPaymentsBtn = document.getElementById('deleteSelectedWaterBillPaymentsBtn');
    const uploadForm = document.getElementById('uploadWaterBillPaymentsForm');
    const uploadMessages = document.getElementById('uploadWaterBillPaymentsMessages');
    const waterBillPaymentsFile = document.getElementById('waterBillPaymentsFile');
    const validateWaterBillPaymentsBtn = document.getElementById('validateWaterBillPaymentsBtn');
    const uploadWaterBillPaymentsBtn = document.getElementById('uploadWaterBillPaymentsBtn');
    const cancelWaterBillPaymentsUploadBtn = document.getElementById('cancelWaterBillPaymentsUploadBtn');
    const bulkGenerateForm = document.getElementById('bulkGenerateWaterBillsForm');
    const bulkGenerateMessages = document.getElementById('bulkGenerateWaterBillsMessages');
    const bulkWaterBillsFile = document.getElementById('bulkWaterBillsFile');
    const validateBulkWaterBillsBtn = document.getElementById('validateBulkWaterBillsBtn');
    const uploadBulkWaterBillsBtn = document.getElementById('uploadBulkWaterBillsBtn');
    const cancelBulkWaterBillsUploadBtn = document.getElementById('cancelBulkWaterBillsUploadBtn');

    function escapeHtml(value) {
        const div = document.createElement('div');
        div.textContent = value;
        return div.innerHTML;
    }

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

    function toggleWaterBillPaymentDeleteButton() {
        const count = document.querySelectorAll('.water-bill-payment-checkbox:checked').length;
        if (deleteSelectedWaterBillPaymentsBtn) {
            deleteSelectedWaterBillPaymentsBtn.style.display = count > 0 ? 'inline-block' : 'none';
        }
    }

    function toggleWaterBillDeleteButton() {
        const count = document.querySelectorAll('.water-bill-checkbox:checked').length;
        if (deleteSelectedWaterBillsBtn) {
            deleteSelectedWaterBillsBtn.style.display = count > 0 ? 'inline-block' : 'none';
        }
    }

    if (selectAllWaterBills) {
        selectAllWaterBills.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('.water-bill-checkbox');
            checkboxes.forEach(checkbox => checkbox.checked = this.checked);
            toggleWaterBillDeleteButton();
        });
    }

    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('water-bill-checkbox')) {
            const checkboxes = document.querySelectorAll('.water-bill-checkbox');
            const checkedCheckboxes = document.querySelectorAll('.water-bill-checkbox:checked');
            if (selectAllWaterBills) {
                selectAllWaterBills.checked = checkboxes.length > 0 && checkboxes.length === checkedCheckboxes.length;
            }
            toggleWaterBillDeleteButton();
        }
    });

    if (deleteSelectedWaterBillsBtn) {
        deleteSelectedWaterBillsBtn.addEventListener('click', function() {
            const selectedIds = Array.from(document.querySelectorAll('.water-bill-checkbox:checked'))
                                     .map(checkbox => checkbox.value);

            if (!selectedIds.length) return;
            if (!confirm(`Delete ${selectedIds.length} water bill(s)?`)) return;
            if (!window.downloadSelectedRowsBeforeDelete('.water-bill-checkbox:checked', 'water-bills-before-delete')) return;

            const formData = new FormData();
            selectedIds.forEach(id => formData.append('bill_ids[]', id));

            fetch('/water_bills/delete/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.reload();
                } else {
                    alert(data.message || 'Failed to delete water bills');
                }
            })
            .catch(error => {
                alert('Error deleting water bills');
            });
        });
    }

    if (selectAllWaterBillPayments) {
        selectAllWaterBillPayments.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('.water-bill-payment-checkbox');
            checkboxes.forEach(checkbox => checkbox.checked = this.checked);
            toggleWaterBillPaymentDeleteButton();
        });
    }

    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('water-bill-payment-checkbox')) {
            const checkboxes = document.querySelectorAll('.water-bill-payment-checkbox');
            const checkedCheckboxes = document.querySelectorAll('.water-bill-payment-checkbox:checked');
            if (selectAllWaterBillPayments) {
                selectAllWaterBillPayments.checked = checkboxes.length > 0 && checkboxes.length === checkedCheckboxes.length;
            }
            toggleWaterBillPaymentDeleteButton();
        }
    });

    if (deleteSelectedWaterBillPaymentsBtn) {
        deleteSelectedWaterBillPaymentsBtn.addEventListener('click', function() {
            const selectedIds = Array.from(document.querySelectorAll('.water-bill-payment-checkbox:checked'))
                                     .map(checkbox => checkbox.value);

            if (!selectedIds.length) return;
            if (!confirm(`Delete ${selectedIds.length} water bill payment(s)?`)) return;
            if (!window.downloadSelectedRowsBeforeDelete('.water-bill-payment-checkbox:checked', 'water-bill-payments-before-delete')) return;

            const formData = new FormData();
            selectedIds.forEach(id => formData.append('payment_ids[]', id));

            fetch('/water_bills/payments/delete/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.reload();
                } else {
                    alert(data.message || 'Failed to delete water bill payments');
                }
            })
            .catch(error => {
                alert('Error deleting water bill payments');
            });
        });
    }

    function showUploadMessage(type, title, messages = []) {
        if (!uploadMessages) return;

        const alertClass = type === 'success' ? 'alert-success' : type === 'info' ? 'alert-info' : 'alert-danger';
        const listHtml = messages.length
            ? `<ul class="mb-0 mt-2">${messages.map(message => `<li>${escapeHtml(message)}</li>`).join('')}</ul>`
            : '';

        uploadMessages.className = `alert ${alertClass}`;
        uploadMessages.innerHTML = `<div class="fw-semibold">${escapeHtml(title)}</div>${listHtml}`;
    }

    function showBulkGenerateMessage(type, title, messages = []) {
        if (!bulkGenerateMessages) return;

        const alertClass = type === 'success' ? 'alert-success' : type === 'info' ? 'alert-info' : 'alert-danger';
        const listHtml = messages.length
            ? `<ul class="mb-0 mt-2">${messages.map(message => `<li>${escapeHtml(message)}</li>`).join('')}</ul>`
            : '';

        bulkGenerateMessages.className = `alert ${alertClass}`;
        bulkGenerateMessages.innerHTML = `<div class="fw-semibold">${escapeHtml(title)}</div>${listHtml}`;
    }

    function resetUploadActions() {
        if (uploadWaterBillPaymentsBtn) {
            uploadWaterBillPaymentsBtn.style.display = 'none';
            uploadWaterBillPaymentsBtn.disabled = false;
            uploadWaterBillPaymentsBtn.textContent = 'Upload';
        }
        if (cancelWaterBillPaymentsUploadBtn) cancelWaterBillPaymentsUploadBtn.style.display = 'none';
        if (validateWaterBillPaymentsBtn) {
            validateWaterBillPaymentsBtn.style.display = 'inline-block';
            validateWaterBillPaymentsBtn.disabled = false;
            validateWaterBillPaymentsBtn.textContent = 'Validate';
        }
        if (uploadMessages) {
            uploadMessages.className = 'alert d-none';
            uploadMessages.innerHTML = '';
        }
    }

    function resetBulkGenerateActions() {
        if (uploadBulkWaterBillsBtn) {
            uploadBulkWaterBillsBtn.style.display = 'none';
            uploadBulkWaterBillsBtn.disabled = false;
            uploadBulkWaterBillsBtn.textContent = 'Upload';
        }
        if (cancelBulkWaterBillsUploadBtn) cancelBulkWaterBillsUploadBtn.style.display = 'none';
        if (validateBulkWaterBillsBtn) {
            validateBulkWaterBillsBtn.style.display = 'inline-block';
            validateBulkWaterBillsBtn.disabled = false;
            validateBulkWaterBillsBtn.textContent = 'Validate';
        }
        if (bulkGenerateMessages) {
            bulkGenerateMessages.className = 'alert d-none';
            bulkGenerateMessages.innerHTML = '';
        }
    }

    function getSelectedBulkWaterBillsFile() {
        const file = bulkWaterBillsFile && bulkWaterBillsFile.files ? bulkWaterBillsFile.files[0] : null;

        if (!file) {
            showBulkGenerateMessage('error', 'Please select a file');
            return null;
        }

        const validTypes = ['text/csv', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'];
        if (!validTypes.includes(file.type) && !file.name.endsWith('.csv') && !file.name.endsWith('.xlsx')) {
            showBulkGenerateMessage('error', 'Please upload a CSV or XLSX file');
            return null;
        }

        return file;
    }

    function postBulkWaterBillsUpload(validateOnly) {
        const file = getSelectedBulkWaterBillsFile();
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);
        formData.append('csrfmiddlewaretoken', bulkGenerateForm.querySelector('[name=csrfmiddlewaretoken]').value);
        if (validateOnly) {
            formData.append('validate_only', '1');
        }

        if (validateOnly && validateBulkWaterBillsBtn) {
            validateBulkWaterBillsBtn.disabled = true;
            validateBulkWaterBillsBtn.textContent = 'Validating...';
        }
        if (!validateOnly && uploadBulkWaterBillsBtn) {
            uploadBulkWaterBillsBtn.disabled = true;
            uploadBulkWaterBillsBtn.textContent = 'Uploading...';
        }

        fetch('/water_bills/bulk-generate/', {
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
                    showBulkGenerateMessage('success', data.message || `Validation complete: ${data.valid_rows || 0} valid, ${data.invalid_rows || 0} invalid.`, detailMessages);
                    if (uploadBulkWaterBillsBtn) {
                        uploadBulkWaterBillsBtn.style.display = 'inline-block';
                        uploadBulkWaterBillsBtn.disabled = false;
                        uploadBulkWaterBillsBtn.textContent = 'Upload';
                    }
                    if (cancelBulkWaterBillsUploadBtn) cancelBulkWaterBillsUploadBtn.style.display = 'inline-block';
                    if (validateBulkWaterBillsBtn) validateBulkWaterBillsBtn.style.display = 'none';
                } else {
                    showBulkGenerateMessage('error', data.message || 'Validation failed', detailMessages);
                    if (uploadBulkWaterBillsBtn) uploadBulkWaterBillsBtn.style.display = 'none';
                    if (cancelBulkWaterBillsUploadBtn) cancelBulkWaterBillsUploadBtn.style.display = 'inline-block';
                    if (validateBulkWaterBillsBtn) {
                        validateBulkWaterBillsBtn.disabled = false;
                        validateBulkWaterBillsBtn.textContent = 'Validate';
                    }
                }
                return;
            }

            if (data.success) {
                showBulkGenerateMessage('success', data.message || `Successfully generated ${data.count} water bill(s)`, detailMessages);
                window.location.reload();
            } else {
                showBulkGenerateMessage('error', data.message || 'Failed to generate water bills', detailMessages);
                if (uploadBulkWaterBillsBtn) {
                    uploadBulkWaterBillsBtn.disabled = false;
                    uploadBulkWaterBillsBtn.textContent = 'Upload';
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showBulkGenerateMessage('error', validateOnly ? 'An error occurred while validating water bills' : 'An error occurred while generating water bills');
            if (validateBulkWaterBillsBtn) {
                validateBulkWaterBillsBtn.disabled = false;
                validateBulkWaterBillsBtn.textContent = 'Validate';
            }
            if (uploadBulkWaterBillsBtn) {
                uploadBulkWaterBillsBtn.disabled = false;
                uploadBulkWaterBillsBtn.textContent = 'Upload';
            }
        });
    }

    function getSelectedWaterBillPaymentFile() {
        const file = waterBillPaymentsFile && waterBillPaymentsFile.files ? waterBillPaymentsFile.files[0] : null;

        if (!file) {
            showUploadMessage('error', 'Please select a file');
            return null;
        }

        const validTypes = ['text/csv', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'];
        if (!validTypes.includes(file.type) && !file.name.endsWith('.csv') && !file.name.endsWith('.xlsx')) {
            showUploadMessage('error', 'Please upload a CSV or XLSX file');
            return null;
        }

        return file;
    }

    function postWaterBillPaymentUpload(validateOnly) {
        const file = getSelectedWaterBillPaymentFile();
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);
        formData.append('csrfmiddlewaretoken', uploadForm.querySelector('[name=csrfmiddlewaretoken]').value);
        if (validateOnly) {
            formData.append('validate_only', '1');
        }

        if (validateOnly && validateWaterBillPaymentsBtn) {
            validateWaterBillPaymentsBtn.disabled = true;
            validateWaterBillPaymentsBtn.textContent = 'Validating...';
        }
        if (!validateOnly && uploadWaterBillPaymentsBtn) {
            uploadWaterBillPaymentsBtn.disabled = true;
            uploadWaterBillPaymentsBtn.textContent = 'Uploading...';
        }

        fetch('/water_bills/upload/', {
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
                    showUploadMessage('success', data.message || `Validation complete: ${data.valid_rows || 0} valid, ${data.invalid_rows || 0} invalid.`, detailMessages);
                    if (uploadWaterBillPaymentsBtn) {
                        uploadWaterBillPaymentsBtn.style.display = 'inline-block';
                        uploadWaterBillPaymentsBtn.disabled = false;
                        uploadWaterBillPaymentsBtn.textContent = 'Upload';
                    }
                    if (cancelWaterBillPaymentsUploadBtn) cancelWaterBillPaymentsUploadBtn.style.display = 'inline-block';
                    if (validateWaterBillPaymentsBtn) validateWaterBillPaymentsBtn.style.display = 'none';
                } else {
                    showUploadMessage('error', data.message || 'Validation failed', detailMessages);
                    if (uploadWaterBillPaymentsBtn) uploadWaterBillPaymentsBtn.style.display = 'none';
                    if (cancelWaterBillPaymentsUploadBtn) cancelWaterBillPaymentsUploadBtn.style.display = 'inline-block';
                    if (validateWaterBillPaymentsBtn) {
                        validateWaterBillPaymentsBtn.disabled = false;
                        validateWaterBillPaymentsBtn.textContent = 'Validate';
                    }
                }
                return;
            }

            if (data.success) {
                showUploadMessage('success', data.message || `Successfully uploaded ${data.count} water bill payments`, detailMessages);
                window.location.reload();
            } else {
                showUploadMessage('error', data.message || 'Failed to upload water bill payments', detailMessages);
                if (uploadWaterBillPaymentsBtn) {
                    uploadWaterBillPaymentsBtn.disabled = false;
                    uploadWaterBillPaymentsBtn.textContent = 'Upload';
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showUploadMessage('error', validateOnly ? 'An error occurred while validating water bill payments' : 'An error occurred while uploading water bill payments');
            if (validateWaterBillPaymentsBtn) {
                validateWaterBillPaymentsBtn.disabled = false;
                validateWaterBillPaymentsBtn.textContent = 'Validate';
            }
            if (uploadWaterBillPaymentsBtn) {
                uploadWaterBillPaymentsBtn.disabled = false;
                uploadWaterBillPaymentsBtn.textContent = 'Upload';
            }
        });
    }

    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            postWaterBillPaymentUpload(true);
        });

        if (uploadWaterBillPaymentsBtn) {
            uploadWaterBillPaymentsBtn.addEventListener('click', function() {
                postWaterBillPaymentUpload(false);
            });
        }

        if (waterBillPaymentsFile) {
            waterBillPaymentsFile.addEventListener('change', resetUploadActions);
        }

        const uploadModal = document.getElementById('uploadModal');
        if (uploadModal) {
            uploadModal.addEventListener('hidden.bs.modal', function() {
                uploadForm.reset();
                resetUploadActions();
            });
        }
    }

    if (bulkGenerateForm) {
        bulkGenerateForm.addEventListener('submit', function(e) {
            e.preventDefault();
            postBulkWaterBillsUpload(true);
        });

        if (uploadBulkWaterBillsBtn) {
            uploadBulkWaterBillsBtn.addEventListener('click', function() {
                postBulkWaterBillsUpload(false);
            });
        }

        if (bulkWaterBillsFile) {
            bulkWaterBillsFile.addEventListener('change', resetBulkGenerateActions);
        }

        const bulkGenerateModal = document.getElementById('bulkGenerateWaterBillModal');
        if (bulkGenerateModal) {
            bulkGenerateModal.addEventListener('hidden.bs.modal', function() {
                bulkGenerateForm.reset();
                resetBulkGenerateActions();
            });
        }
    }
});
