document.addEventListener('DOMContentLoaded', () => {
  const typeSelect      = document.getElementById('type');
  const sharedSection   = document.getElementById('sharedSection');
  const groupSelect     = document.getElementById('group');
  const groupSection    = document.getElementById('groupSection');
  const noGroupsAlert   = document.getElementById('noGroups');
  const receiptGroup    = document.getElementById('receiptGroup');
  const amountInput     = document.getElementById('amount');
  const form            = document.getElementById('expenseForm');
  const paidBySelect    = document.getElementById('paidBy');

  let myGroups = [];

  async function loadGroups() {
    try {
      const res = await fetch('/api/shared/groups');
      const groups = await res.json();
      myGroups = groups;
      groupSelect.innerHTML = '';
      if (groups.length === 0) {
        noGroupsAlert.style.display = 'block';
        groupSection.style.display = 'none';
      } else {
        noGroupsAlert.style.display = 'none';
        groupSection.style.display = 'block';
        groups.forEach(g => {
          groupSelect.add(new Option(g.name, g.id));
        });

        // 🔁 Trigger change to load members into paidBySelect
        groupSelect.dispatchEvent(new Event('change'));
      }
    } catch (err) {
      console.error('Failed to load groups', err);
    }
  }

  // Show/hide shared-specific fields
function toggleTypeFields() {
  const isShared = typeSelect.value === 'shared';
  sharedSection.style.display  = isShared ? 'block' : 'none';
  receiptGroup.style.display   = isShared ? 'block' : 'none';
  amountInput.required         = !isShared;

  //
  if (isShared && groupSelect.options.length > 0) {
    groupSelect.dispatchEvent(new Event('change'));
  }
}

  typeSelect.addEventListener('change', toggleTypeFields);
  toggleTypeFields();

  // Populate paidBy when group changes
  groupSelect.addEventListener('change', () => {
    const groupId = parseInt(groupSelect.value);
    const group = myGroups.find(g => g.id === groupId);

    paidBySelect.innerHTML = '';
    if (group) {
      group.members.forEach(m => {
        paidBySelect.add(new Option(m.username, m.id));
      });
    }
  });

  loadGroups();

  // Handle form submission
  form.addEventListener('submit', async e => {
    e.preventDefault();

    const type        = typeSelect.value;
    const amount      = parseFloat(amountInput.value);
    const description = document.getElementById('description').value;
    const date        = document.getElementById('date').value;
    const notes       = document.getElementById('notes').value;

    if (type === 'shared') {
      if (isNaN(amount)) {
        alert('Please enter an amount.');
        return;
      }

      const payload = {
        description,
        amount,
        date,
        group_id: groupSelect.value,
        paid_by: paidBySelect.value,
        context: notes
      };

      try {
        const res = await fetch('/api/shared/expense', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (!res.ok) {
          alert(data.error || 'Failed to submit shared expense');
          return;
        }

        // 💥 Show backend-calculated split
        let output = '<h5>Resulting split:</h5><ul>';
        Object.entries(data.splits).forEach(([uid, amount]) => {
          const user = myGroups
            .find(g => g.id == groupSelect.value)
            ?.members.find(u => u.id == uid);
          const label = user?.username || `User ${uid}`;
          const dir = amount > 0 ? 'owes' : 'is owed';
          output += `<li>${label} ${dir} $${Math.abs(amount).toFixed(2)}</li>`;
        });
        output += '</ul>';
        document.getElementById('resultMessage').innerHTML = output;

      } catch (err) {
        console.error(err);
        alert('An unexpected error occurred');
      }

    } else {
      const payload = {
        amount,
        description,
        transaction_date: date,
        notes
      };

      try {
        const res = await fetch('/api/personal/expenses', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (res.ok) {
          document.getElementById('resultMessage').textContent = 'Personal expense added!';
        } else {
          alert(data.error || 'Failed to submit personal expense');
        }
      } catch (err) {
        console.error(err);
        alert('An unexpected error occurred');
      }
    }
  });
});
