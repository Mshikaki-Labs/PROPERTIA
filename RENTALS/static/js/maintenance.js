document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('addMaintenanceForm');
    const modal = document.getElementById('addMaintenanceModal');
    const messageDiv = document.getElementById('maintenanceMessage');

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

    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(form);
            formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));

            fetch("/maintenance/create/", {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
            .then(async response => {
                const contentType = response.headers.get('content-type') || '';
                const isJson = contentType.includes('application/json');
                let data = null;
                if (isJson) {
                    data = await response.json();
                } else {
                    data = { success: false, message: `Server error: ${response.status} ${response.statusText}` };
                }

                if (data.success) {
                    messageDiv.className = 'alert alert-success';
                    messageDiv.textContent = data.message;
                    messageDiv.style.display = 'block';
                    form.reset();
                    setTimeout(function() {
                        modal.hide();
                        messageDiv.style.display = 'none';
                        window.location.reload();
                    }, 1000);
                } else {
                    messageDiv.className = 'alert alert-danger';
                    if (data.errors && Object.keys(data.errors).length) {
                        const fieldErrors = Object.entries(data.errors)
                            .map(([field, msgs]) => `${field}: ${Array.isArray(msgs) ? msgs.join(', ') : msgs}`)
                            .join('\n');
                        messageDiv.textContent = (data.message || 'Please fix the errors below') + '\n' + fieldErrors;
                    } else {
                        messageDiv.textContent = data.message || 'Failed to add maintenance';
                    }
                    messageDiv.style.display = 'block';
                }
            })
            .catch(error => {
                messageDiv.className = 'alert alert-danger';
                messageDiv.textContent = 'An error occurred: ' + (error.message || error);
                messageDiv.style.display = 'block';
            });
        });
    }

    if (modal) {
        modal.addEventListener('hidden.bs.modal', function() {
            form.reset();
            messageDiv.style.display = 'none';
        });
    }

    function isCompletedPage() {
        return window.location.pathname.includes('/maintenance/completed');
    }

    document.querySelectorAll('.status-select').forEach(function(select) {
        select.addEventListener('change', function() {
            const id = this.getAttribute('data-id');
            const newStatus = this.value;
            const row = this.closest('tr');

            fetch(`/maintenance/toggle-status/${id}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(async response => {
                const data = await response.json();
                if (data.success) {
                    this.setAttribute('data-status', data.status);
                    this.value = data.status;
                    if ((isCompletedPage() && data.status === 'pending') || (!isCompletedPage() && data.status === 'completed')) {
                        row.style.transition = 'opacity 0.4s';
                        row.style.opacity = '0';
                        setTimeout(function() {
                            row.remove();
                        }, 400);
                    }
                } else {
                    this.value = this.getAttribute('data-status');
                    alert(data.message || 'Failed to update status');
                }
            })
            .catch(error => {
                this.value = this.getAttribute('data-status');
                alert('An error occurred: ' + (error.message || error));
            });
        });
    });

    document.querySelectorAll('.receipt-form').forEach(function(form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const id = this.getAttribute('data-id');
            const formData = new FormData(this);
            formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));

            fetch(`/maintenance/attach-receipt/${id}/`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
            .then(async response => {
                const data = await response.json();
                const messageDiv = document.getElementById(`receiptMessage${id}`);
                if (data.success) {
                    messageDiv.className = 'alert alert-success';
                    messageDiv.textContent = data.message;
                    messageDiv.style.display = 'block';
                    setTimeout(function() {
                        const modalEl = document.getElementById(`receiptModal${id}`);
                        const modal = bootstrap.Modal.getInstance(modalEl);
                        modal.hide();
                        messageDiv.style.display = 'none';
                        window.location.reload();
                    }, 1000);
                } else {
                    messageDiv.className = 'alert alert-danger';
                    messageDiv.textContent = data.message || 'Failed to attach receipt';
                    messageDiv.style.display = 'block';
                }
            })
            .catch(error => {
                const messageDiv = document.getElementById(`receiptMessage${id}`);
                messageDiv.className = 'alert alert-danger';
                messageDiv.textContent = 'An error occurred: ' + (error.message || error);
                messageDiv.style.display = 'block';
            });
        });
    });
});

// ======================
// DELETE MAINTENANCE FUNCTIONALITY
// ======================

(function() {
    const maintenancePage = document.getElementById('maintenancePage');
    const deleteMaintenanceUrl = maintenancePage ? maintenancePage.dataset.deleteUrl : '/maintenance/delete/';
    const selectAllCheckbox = document.getElementById('selectAllCheckbox');
    const maintenanceCheckboxes = document.querySelectorAll('.maintenance-checkbox');
    const deleteSelectedBtn = document.getElementById('deleteSelectedBtn');

    if (selectAllCheckbox && maintenanceCheckboxes.length) {
        selectAllCheckbox.addEventListener('change', function() {
            maintenanceCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateDeleteButton();
        });

        maintenanceCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', updateDeleteButton);
        });

        function updateDeleteButton() {
            const anySelected = Array.from(maintenanceCheckboxes).some(cb => cb.checked);
            deleteSelectedBtn.style.display = anySelected ? 'inline-block' : 'none';
        }

        deleteSelectedBtn.addEventListener('click', function() {
            const selectedIds = Array.from(maintenanceCheckboxes)
                .filter(cb => cb.checked)
                .map(cb => cb.value);

            if (selectedIds.length === 0) {
                alert('Please select at least one maintenance record to delete');
                return;
            }

            if (confirm(`Are you sure you want to delete ${selectedIds.length} maintenance record/s? This action cannot be undone.`)) {
                if (!window.downloadSelectedRowsBeforeDelete('.maintenance-checkbox:checked', 'maintenance-before-delete')) return;

                const formData = new FormData();
                selectedIds.forEach(id => formData.append('maintenance_ids[]', id));

                fetch(deleteMaintenanceUrl, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value || '',
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
                        alert(data.message || 'Failed to delete maintenance');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred while deleting maintenance');
                });
            }
        });
    }
})();
