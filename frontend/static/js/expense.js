// static/js/expense.js

document.addEventListener('DOMContentLoaded', () => {
    const typeSelect    = document.getElementById('type');
    const sharedFields  = document.getElementById('sharedFields');
    const groupSelect   = document.getElementById('group');
    const excludeSelect = document.getElementById('exclude');
    const form          = document.getElementById('expenseForm');
  
    // 1) Toggle shared-only fields
    typeSelect.addEventListener('change', () => {
      sharedFields.style.display = (typeSelect.value === 'shared') ? 'block' : 'none';
    });
  
    // 2) Populate groups & exclude options
    async function loadGroups() {
      try {
        const res = await fetch('/api/shared/groups');
        const groups = await res.json();
        groups.forEach(g => {
          const opt1 = new Option(g.name, g.id);
          groupSelect.add(opt1);
          const opt2 = new Option(g.name, g.id);
          excludeSelect.add(opt2);
        });
      } catch (err) {
        console.error('Error loading groups', err);
      }
    }
    loadGroups();
  
    // 3) Handle form submission
    form.addEventListener('submit', async e => {
      e.preventDefault();
  
      const type        = typeSelect.value;
      const amount      = parseFloat(document.getElementById('amount').value);
      const description = document.getElementById('description').value;
      const date        = document.getElementById('date').value;
      const recurring   = document.getElementById('recurring').checked;
      const notes       = document.getElementById('notes').value;
  
      let url, options;
  
      if (type === 'personal') {
        url = '/api/personal/expenses';
        options = {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ amount, description, date, recurring, notes })
        };
      } else {
        url = '/api/shared/expense';
        const formData = new FormData();
        formData.append('amount', amount);
        formData.append('description', description);
        formData.append('date', date);
        formData.append('recurring', recurring);
        formData.append('notes', notes);
        formData.append('group_id', groupSelect.value);
        Array.from(excludeSelect.selectedOptions).forEach(opt =>
          formData.append('exclude_members', opt.value)
        );
        const receiptFile = document.getElementById('receipt').files[0];
        if (receiptFile) formData.append('receipt', receiptFile);
  
        options = { method: 'POST', body: formData };
      }
  
      try {
        const res = await fetch(url, options);
        const data = await res.json();
        if (res.ok) {
          window.location.href = '/dashboard';
        } else {
          alert(data.error || 'Failed to submit expense');
        }
      } catch (err) {
        console.error(err);
        alert('An unexpected error occurred');
      }
    });
  });
  