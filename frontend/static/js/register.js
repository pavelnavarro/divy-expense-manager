// frontend/static/js/register.js

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('register-form');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const data = {
      username: form.username.value,
      email: form.email.value,
      password: form.password.value
    };

    const resp = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(data)
    });

    if (resp.ok) {
      alert('Registered! Please log in.');
      window.location.href = '/login';
    } else {
      const err = await resp.json();
      alert('Registration failed: ' + (err.error || resp.statusText));
    }
  });
});
