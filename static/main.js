// static/main.js

const API_BASE_URL = 'http://63.181.97.82';

document.addEventListener('DOMContentLoaded', () => {
    const logoutButton = document.getElementById('logoutButton');
    const loginLink = document.getElementById('loginLink');
    const registerLink = document.getElementById('registerLink');
    const welcomeMessage = document.getElementById('welcomeMessage');

    function getAccessToken() {
        return localStorage.getItem('accessToken');
    }

    function checkLoginStatus() {
        const token = getAccessToken();
        if (token) {
            try {
                const base64Url = token.split('.')[1];
                const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
                const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
                    return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
                }).join(''));
                const payload = JSON.parse(jsonPayload);

                if (welcomeMessage) welcomeMessage.textContent = `Welcome, ${payload.sub}!`;
                if (welcomeMessage) welcomeMessage.style.display = 'inline';
                if (logoutButton) logoutButton.style.display = 'inline';
                if (loginLink) loginLink.style.display = 'none';
                if (registerLink) registerLink.style.display = 'none';

            } catch (e) {
                console.error("Failed to decode token:", e);
                logout();
            }
        } else {
            if (welcomeMessage) welcomeMessage.style.display = 'none';
            if (logoutButton) logoutButton.style.display = 'none';
            if (loginLink) loginLink.style.display = 'inline';
            if (registerLink) registerLink.style.display = 'inline';
        }
    }

    function logout() {
        localStorage.removeItem('accessToken');
        // Redirect to the login page from anywhere
        window.location.href = '/static/login.html';
    }

    if (logoutButton) {
        logoutButton.addEventListener('click', logout);
    }

    // Check login status on every page that includes this script
    checkLoginStatus();
});