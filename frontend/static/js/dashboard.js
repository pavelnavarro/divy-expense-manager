// static/js/dashboard.js

document.addEventListener("DOMContentLoaded", () => {
  fetch("/dashboard", {
    method: "GET",
    credentials: 'include'  // ← cookie will be sent
  })
  .then(res => {
    if (res.status === 401) {
      window.location.href = "/login";
      return;
    }
    return res.text();
  })
  .then(html => {
    if (html) document.body.innerHTML = html;
  });
});
