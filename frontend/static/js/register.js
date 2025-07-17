// static/js/register.js

document
  .getElementById('registerForm')
  .addEventListener('submit', async function (e) {
    e.preventDefault(); // stop the normal form submit

    // grab values
    const username = document.getElementById('username').value;
    const email    = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    // send to your API endpoint
    const response = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email, password })
    });

    const data = await response.json();

    if (response.ok) {
      // on success, send user to login
      window.location.href = '/login';
    } else {
      // show error without reloading
      alert(data.error || 'Registration failed');
    }
  });
