document.addEventListener('DOMContentLoaded', () => {
  const typeSelect           = document.getElementById('type');
  const sharedSection        = document.getElementById('sharedSection');
  const groupSelect          = document.getElementById('group');
  const groupSection         = document.getElementById('groupSection');
  const noGroupsAlert        = document.getElementById('noGroups');
  const receiptGroup         = document.getElementById('receiptGroup');
  const amountInput          = document.getElementById('amount');
  const geminiResponseGroup  = document.getElementById('geminiResponseGroup');
  const form                 = document.getElementById('expenseForm');

  async function loadGroups() {
    try {
      const res = await fetch('/api/shared/groups');
      const groups = await res.json();
      groupSelect.innerHTML = ''; // clear
      if (groups.length === 0) {
        noGroupsAlert.style.display = 'block';
        groupSection.style.display = 'none';
      } else {
        noGroupsAlert.style.display = 'none';
        groupSection.style.display = 'block';
        groups.forEach(g => {
          const opt = new Option(g.name, g.id);
          groupSelect.add(opt);
        });
      }
    } catch (err) {
      console.error('Failed to load groups', err);
    }
  }

  function toggleTypeFields() {
    const isShared = typeSelect.value === 'shared';
    sharedSection.style.display        = isShared ? 'block' : 'none';
    receiptGroup.style.display         = isShared ? 'block' : 'none';
    amountInput.required               = !isShared;
  }

  typeSelect.addEventListener('change', toggleTypeFields);
  toggleTypeFields();  // initial
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
        formData.append('context', notes);
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
          const data = await res.json();
          const splits = data.splits;
          
          let output = '<h5>Suggested Split:</h5><ul>';
          for (const [name, amt] of Object.entries(splits)) {
            output += `<li>${name}: $${amt.toFixed(2)}</li>`;
          }
          output += '</ul>';

          document.getElementById('resultMessage').innerHTML = output;
        } else {
          alert(data.error || 'Failed to submit expense');
        }
      } catch (err) {
        console.error(err);
        alert('An unexpected error occurred');
      }
    });
  });
  