// Handle login form submission
document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            try {
                const response = await fetch('/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ username, password })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    // Store the token in localStorage
                    localStorage.setItem('jwt_token', data.access_token);
                    // Add token to default headers for future requests
                    setupAxiosInterceptors();
                    // Redirect to dashboard
                    window.location.href = '/';
                } else {
                    // Display error message
                    const errorElement = document.getElementById('error-message');
                    if (errorElement) {
                        errorElement.textContent = data.msg || 'Login failed';
                        errorElement.style.display = 'block';
                    }
                }
            } catch (error) {
                console.error('Login error:', error);
            }
        });
    }
});

// Setup axios interceptors for automatic token inclusion
function setupAxiosInterceptors() {
    // Add a request interceptor
    axios.interceptors.request.use(function (config) {
        const token = localStorage.getItem('jwt_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    }, function (error) {
        return Promise.reject(error);
    });

    // Add a response interceptor
    axios.interceptors.response.use(function (response) {
        return response;
    }, function (error) {
        if (error.response.status === 401) {
            // If the token is invalid or expired, redirect to login
            localStorage.removeItem('jwt_token');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    });
}

// Check authentication status on page load
document.addEventListener('DOMContentLoaded', function() {
    const token = localStorage.getItem('jwt_token');
    if (token) {
        setupAxiosInterceptors();
    } else if (window.location.pathname !== '/login') {
        window.location.href = '/login';
    }
});