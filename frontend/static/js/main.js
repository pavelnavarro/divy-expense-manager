// Add your frontend JS here
document.getElementById('loginForm').addEventListener('submit', async function (e) {
    e.preventDefault();
  
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
  
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
  
    const data = await response.json();
  
    if (response.ok) {
      localStorage.setItem('access_token', data.access_token);
      window.location.href = '/dashboard';
    } else {
      alert(data.error || 'Login failed');
    }
  });