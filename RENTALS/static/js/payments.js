document.addEventListener('DOMContentLoaded', function() {
    const selectAllBtn = document.getElementById('selectAllPayments');
    const deleteBtn = document.getElementById('deleteSelectedPaymentsBtn');

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
            const checkboxes = document.querySelectorAll('.payment-checkbox');
            checkboxes.forEach(cb => cb.checked = this.checked);
            toggleDeleteButton();
        });
    }

    // 3. Individual checkbox logic (using delegation)
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('payment-checkbox')) {
            const allCheckboxes = document.querySelectorAll('.payment-checkbox');
            const checkedCheckboxes = document.querySelectorAll('.payment-checkbox:checked');
            
            // Sync the "Select All" checkbox state
            if (selectAllBtn) {
                selectAllBtn.checked = allCheckboxes.length === checkedCheckboxes.length;
            }
            toggleDeleteButton();
        }
    });

    function toggleDeleteButton() {
        const count = document.querySelectorAll('.payment-checkbox:checked').length;
        if (deleteBtn) {
            deleteBtn.style.display = count > 0 ? 'inline-block' : 'none';
        }
    }

    // 4. The Delete Fetch
    if (deleteBtn) {
        deleteBtn.addEventListener('click', function() {
            const selectedIds = Array.from(document.querySelectorAll('.payment-checkbox:checked'))
                                     .map(cb => cb.value);

            if (!confirm(`Delete ${selectedIds.length} payment(s)?`)) return;

            const formData = new FormData();
            selectedIds.forEach(id => formData.append('payment_ids[]', id));

            // USE THE ABSOLUTE PATH matching your urls.py
            fetch('/payments/delete/', { 
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

    // 5. Handle Add Payment Form
    const addPaymentForm = document.getElementById('addPaymentForm');
    
    if (addPaymentForm) {
        addPaymentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            
            fetch('', {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
            .then(response => response.text())
            .then(html => {
                // Check if response contains form errors
                if (html.includes('errorlist') || html.includes('This field is required')) {
                    // Display errors in modal
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');
                    const errorElements = doc.querySelectorAll('ul.errorlist');
                    
                    let errorHtml = '<ul>';
                    errorElements.forEach(el => {
                        const items = el.querySelectorAll('li');
                        items.forEach(item => {
                            errorHtml += '<li>' + item.textContent + '</li>';
                        });
                    });
                    errorHtml += '</ul>';
                    
                    if (errorElements.length > 0) {
                        document.getElementById('paymentErrors').innerHTML = errorHtml;
                        document.getElementById('paymentErrors').style.display = 'block';
                    } else {
                        location.reload();
                    }
                } else {
                    // Success - reload page
                    location.reload();
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred');
            });
        });
    }
    
    // 6. Handle Upload Payments Form
    const uploadForm = document.getElementById('uploadPaymentsForm');
    
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const fileInput = document.getElementById('paymentsFile');
            const file = fileInput.files[0];
            
            if (!file) {
                alert('Please select a file');
                return;
            }
            
            // Validate file type
            const validTypes = ['text/csv', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'];
            if (!validTypes.includes(file.type) && !file.name.endsWith('.csv') && !file.name.endsWith('.xlsx')) {
                alert('Please upload a CSV or XLSX file');
                return;
            }
            
            const formData = new FormData();
            formData.append('file', file);
            formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
            
            fetch('/payments/upload/', {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    let message = `Successfully uploaded ${data.count} payments`;
                    if (data.errors && data.errors.length) {
                        message += '\n\nWarnings:\n' + data.errors.slice(0, 5).join('\n');
                    }
                    alert(message);
                    location.reload();
                } else {
                    let errorMsg = data.message || 'Failed to upload payments';
                    if (data.errors && data.errors.length) {
                        errorMsg += '\n\n' + data.errors.slice(0, 5).join('\n');
                    }
                    alert(errorMsg);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while uploading payments');
            });
        });
    }
});
