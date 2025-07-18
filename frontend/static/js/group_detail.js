document.addEventListener('DOMContentLoaded', () => {
  const groupId         = window.location.pathname.split('/').pop();
  const groupNameEl     = document.getElementById('groupName');
  const groupCreatorEl  = document.getElementById('groupCreator');
  const memberList      = document.getElementById('memberList');
  const balancesBody    = document.getElementById('balancesTableBody');
  const paymentsBody    = document.getElementById('paymentsTableBody');
  const recordBtn       = document.getElementById('recordPaymentBtn');
  const paymentModal    = document.getElementById('paymentModal');
  const closeModal      = document.getElementById('closePaymentModal');
  const paymentForm     = document.getElementById('paymentForm');
  const fromUserSelect  = document.getElementById('fromUser');
  const toUserSelect    = document.getElementById('toUser');

  let groupMembers = [];

  async function loadGroup() {
    const res = await fetch(`/api/shared/group/${groupId}`);
    const g   = await res.json();

    groupNameEl.textContent = g.name;
    groupCreatorEl.textContent = g.members.find(u => u.id === g.created_by)?.username || '—';
    groupMembers = g.members;

    g.members.forEach(m => {
      const li = document.createElement('li');
      li.textContent = m.username;
      memberList.appendChild(li);

      fromUserSelect.add(new Option(m.username, m.id));
      toUserSelect.add(new Option(m.username, m.id));
    });
  }

  async function loadBalances() {
    const res = await fetch(`/api/shared/group/${groupId}/balances`);
    const { net_balances } = await res.json();

    balancesBody.innerHTML = '';
    for (const [uid, amount] of Object.entries(net_balances)) {
      const user = groupMembers.find(u => u.id == uid);
      const tr = document.createElement('tr');
      const tdName = document.createElement('td');
      const tdAmount = document.createElement('td');

      tdName.textContent = user?.username || `User ${uid}`;
      tdAmount.textContent = amount >= 0
        ? `is owed $${amount.toFixed(2)}`
        : `owes $${Math.abs(amount).toFixed(2)}`;

      tr.appendChild(tdName);
      tr.appendChild(tdAmount);
      balancesBody.appendChild(tr);
    }
  }

  async function loadPayments() {
    const res = await fetch(`/api/shared/group/${groupId}/history`);
    const { payments } = await res.json();

    paymentsBody.innerHTML = payments.map(p => `
      <tr>
        <td>${p.from_username || p.from_user}</td>
        <td>${p.to_username || p.to_user}</td>
        <td>$${p.amount.toFixed(2)}</td>
        <td>${p.date}</td>
        <td>${p.status}</td>
      </tr>
    `).join('');
  }

  recordBtn.addEventListener('click', () => {
    paymentModal.style.display = 'block';
  });

  closeModal.addEventListener('click', () => {
    paymentModal.style.display = 'none';
  });

  window.addEventListener('click', e => {
    if (e.target === paymentModal) paymentModal.style.display = 'none';
  });

  paymentForm.addEventListener('submit', async e => {
    e.preventDefault();
    const payload = {
      from_user: document.getElementById('fromUser').value,
      to_user:   document.getElementById('toUser').value,
      amount:    parseFloat(document.getElementById('paymentAmount').value),
      date:      document.getElementById('paymentDate').value
    };
    const res = await fetch(`/api/shared/group/${groupId}/pay`, {
      method:  'POST',
      headers: {'Content-Type':'application/json'},
      body:    JSON.stringify(payload)
    });
    if (res.ok) {
      paymentModal.style.display = 'none';
      loadPayments();
      loadBalances();
    } else {
      alert((await res.json()).error || 'Payment failed');
    }
  });

  loadGroup().then(() => {
    loadBalances();
    loadPayments();
  });
});
