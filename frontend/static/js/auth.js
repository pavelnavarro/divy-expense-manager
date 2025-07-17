// frontend/static/js/auth.js

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('login-form');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Use email field as username for login
    const username = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    const resp = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ username, password })
    });

    if (resp.ok) {
      window.location.href = '/dashboard';
    } else {
      const err = await resp.json();
      alert('Login failed: ' + (err.error || resp.statusText));
    }
  });
});
