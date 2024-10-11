// login.js
document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const usernameInput = document.getElementById('id_username');
    const passwordInput = document.getElementById('id_password');
    const alertDiv = document.getElementById('alert');

    loginForm.addEventListener('submit', function(e) {
        e.preventDefault();

        if (!usernameInput.value || !passwordInput.value) {
            showAlert('Please enter both username and password.');
            return;
        }

        // If validation passes, submit the form
        this.submit();
    });

    function showAlert(message) {
        alertDiv.innerHTML = `<p>${message}</p>`;
        alertDiv.style.display = 'block';

        setTimeout(() => {
            alertDiv.style.display = 'none';
        }, 5000);
    }

    // Clear alert when inputs change
    usernameInput.addEventListener('input', clearAlert);
    passwordInput.addEventListener('input', clearAlert);

    function clearAlert() {
        alertDiv.style.display = 'none';
    }
});