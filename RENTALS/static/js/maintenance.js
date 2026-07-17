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
});
