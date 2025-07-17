// static/js/group_detail.js

document.addEventListener('DOMContentLoaded', () => {
    const groupId = window.location.pathname.split('/').pop();
    const groupNameEl    = document.getElementById('groupName');
    const groupCreatorEl = document.getElementById('groupCreator');
    const memberList     = document.getElementById('memberList');
    const expensesBody   = document.getElementById('expensesTableBody');
    const paymentsBody   = document.getElementById('paymentsTableBody');
    const recordBtn      = document.getElementById('recordPaymentBtn');
    const paymentModal   = document.getElementById('paymentModal');
    const closeModal     = document.getElementById('closePaymentModal');
    const paymentForm    = document.getElementById('paymentForm');
    const fromUserSelect = document.getElementById('fromUser');
    const toUserSelect   = document.getElementById('toUser');
  
    // 1) Load group info (name, creator, members)
    async function loadGroup() {
      const res = await fetch(`/api/shared/group/${groupId}`);
      const g   = await res.json();
      groupNameEl.textContent    = g.name;
      groupCreatorEl.textContent = g.creator.username;
      g.members.forEach(m => {
        const li = document.createElement('li');
        li.textContent = m.username;
        memberList.append(li);
  
        // also populate payment selects
        const opt1 = new Option(m.username, m.id);
        fromUserSelect.add(opt1);
        const opt2 = new Option(m.username, m.id);
        toUserSelect.add(opt2);
      });
    }
  
    // 2) Load expenses history
    async function loadExpenses() {
      const res  = await fetch(`/api/shared/group/${groupId}/history`);
      const data = await res.json();
      expensesBody.innerHTML = data.map(e => `
        <tr>
          <td>${e.description}</td>
          <td>$${e.amount.toFixed(2)}</td>
          <td>${e.paid_by.username}</td>
          <td>${e.notes || ''}</td>
          <td>${e.date}</td>
          <td><button data-id="${e.id}" class="delete-expense">Delete</button></td>
        </tr>
      `).join('');
  
      // attach delete handlers
      document.querySelectorAll('.delete-expense').forEach(btn => {
        btn.addEventListener('click', async () => {
          if (!confirm('Delete this expense?')) return;
          const res = await fetch(`/api/shared/expense/${btn.dataset.id}`, { method: 'DELETE' });
          if (res.ok) loadExpenses();
          else alert('Failed to delete');
        });
      });
    }
  
    // 3) Load payments
    async function loadPayments() {
      const res  = await fetch(`/api/shared/group/${groupId}/balances`);
      const data = await res.json();
      paymentsBody.innerHTML = data.transactions.map(t => `
        <tr>
          <td>${t.from.username}</td>
          <td>${t.to.username}</td>
          <td>$${t.amount.toFixed(2)}</td>
          <td>${t.date}</td>
          <td>${t.status}</td>
        </tr>
      `).join('');
    }
  
    // 4) Modal open/close
    recordBtn.addEventListener('click', () => paymentModal.style.display = 'block');
    closeModal.addEventListener('click', () => paymentModal.style.display = 'none');
    window.addEventListener('click', e => { if (e.target === paymentModal) paymentModal.style.display = 'none' });
  
    // 5) Handle payment form
    paymentForm.addEventListener('submit', async e => {
      e.preventDefault();
      const payload = {
        from: document.getElementById('fromUser').value,
        to:   document.getElementById('toUser').value,
        amount: parseFloat(document.getElementById('paymentAmount').value),
        date: document.getElementById('paymentDate').value
      };
      const res = await fetch(`/api/shared/group/${groupId}/pay`, {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        paymentModal.style.display = 'none';
        loadPayments();
      } else {
        alert((await res.json()).error || 'Payment failed');
      }
    });
  
    // init
    loadGroup();
    loadExpenses();
    loadPayments();
  });
  