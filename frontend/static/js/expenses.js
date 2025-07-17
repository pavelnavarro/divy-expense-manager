// static/js/expenses.js

document.addEventListener('DOMContentLoaded', () => {
    const tabPersonal   = document.getElementById('tabPersonal');
    const tabShared     = document.getElementById('tabShared');
    const filterDate    = document.getElementById('filterDate');
    const expenseList   = document.getElementById('expenseList');
    let currentTab      = 'personal';
  
    // Render table of expenses
    function renderExpenses(items) {
      if (!items || items.length === 0) {
        expenseList.innerHTML = '<p>No expenses found.</p>';
        return;
      }
  
      const rows = items.map(exp => `
        <tr>
          <td>${exp.description}</td>
          <td>$${exp.amount.toFixed(2)}</td>
          <td>${exp.category || ''}</td>
          <td>${exp.date}</td>
          <td>
            <button data-id="${exp.id}" class="delete-btn">Delete</button>
          </td>
        </tr>
      `).join('');
  
      expenseList.innerHTML = `
        <table>
          <thead>
            <tr>
              <th>Description</th>
              <th>Amount</th>
              <th>Category</th>
              <th>Date</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      `;
  
      // Attach delete handlers
      expenseList.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
          const id = btn.dataset.id;
          const url = currentTab === 'personal'
            ? `/api/personal/expenses/${id}`
            : `/api/shared/expense/${id}`;
  
          if (confirm('Delete this expense?')) {
            const res = await fetch(url, { method: 'DELETE' });
            if (res.ok) loadExpenses();
            else alert('Failed to delete');
          }
        });
      });
    }
  
    // Fetch & display based on current tab (and filter date if set)
    async function loadExpenses() {
      expenseList.innerHTML = '<p>Loading...</p>';
      const dateParam = filterDate.value ? `?date=${filterDate.value}` : '';
      const url = currentTab === 'personal'
        ? `/api/personal/expenses${dateParam}`
        : `/api/shared/group/1/history${dateParam}`; // replace 1 with actual group_id as needed
  
      try {
        const res  = await fetch(url);
        const data = await res.json();
        renderExpenses(data);
      } catch (err) {
        expenseList.innerHTML = '<p>Error loading expenses</p>';
        console.error(err);
      }
    }
  
    // Tab click handlers
    tabPersonal.addEventListener('click', () => {
      currentTab = 'personal';
      tabPersonal.classList.add('active');
      tabShared.classList.remove('active');
      loadExpenses();
    });
    tabShared.addEventListener('click', () => {
      currentTab = 'shared';
      tabShared.classList.add('active');
      tabPersonal.classList.remove('active');
      loadExpenses();
    });
  
    // Date filter handler
    filterDate.addEventListener('change', loadExpenses);
  
    // Initial load
    loadExpenses();
  });
  