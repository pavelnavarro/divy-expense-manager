// static/js/auth.js

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('login-form');
  form.addEventListener('submit', async e => {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    const resp = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',           // ← important!
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
