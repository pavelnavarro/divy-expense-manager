document.addEventListener('DOMContentLoaded', () => {
  const addMemberBtn = document.getElementById('addMemberBtn');
  const memberFields = document.getElementById('memberFields');
  const modal = document.getElementById('createGroupModal');
  let allUsers = [];  // will hold fetched users

  // 
  document.getElementById('createGroupBtn').addEventListener('click', () => {
    modal.style.display = 'block';
  });

  // =
  document.getElementById('closeGroupModal').addEventListener('click', () => {
    modal.style.display = 'none';
  });

  // 
  async function loadMembers() {
    try {
      const res = await fetch('/api/shared/users');
      allUsers = await res.json();
    } catch (err) {
      console.error('Could not load users', err);
    }
  }

  // 
  function makeMemberSelect() {
    const wrapper = document.createElement('div');
    wrapper.className = 'member-row';

    const sel = document.createElement('select');
    sel.name = 'members';
    sel.required = true;

    allUsers.forEach(u => {
      if (u.id === CURRENT_USER_ID) return; // 
      const opt = new Option(u.username, u.id);
      sel.add(opt);
    });

    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.textContent = '×';
    removeBtn.addEventListener('click', () => wrapper.remove());

    wrapper.appendChild(sel);
    wrapper.appendChild(removeBtn);
    return wrapper;
  }

  addMemberBtn.addEventListener('click', () => {
    memberFields.appendChild(makeMemberSelect());
  });

  // 
  const form = document.getElementById('createGroupForm');
  form.addEventListener('submit', async e => {
    e.preventDefault();
    const name = document.getElementById('groupName').value;
    const members = Array.from(
      memberFields.querySelectorAll('select[name="members"]')
    ).map(s => parseInt(s.value));

    try {
      const res = await fetch('/api/shared/groups', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, members })
      });
      if (res.ok) {
        modal.style.display = 'none';
        form.reset();
        memberFields.innerHTML = '';
        await loadGroups();
      } else {
        const err = await res.json();
        alert(err.error || 'Failed to create group');
      }
    } catch (err) {
      console.error(err);
      alert('Error creating group');
    }
  });

  //
  loadMembers().then(() => {
    addMemberBtn.click();  //
  });
  loadGroups(); // 
});

// 
async function loadGroups() {
  try {
    const res = await fetch('/api/shared/groups', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    const groups = await res.json();

    const container = document.getElementById('groupsList');
    container.innerHTML = '';

    if (!Array.isArray(groups) || groups.length === 0) {
      container.textContent = 'You are not part of any group yet.';
      return;
    }

    groups.forEach(group => {
      const div = document.createElement('div');
      div.className = 'group-item';
      div.innerHTML = `
        <h4><a href="/group/${group.id}">${group.name}</a></h4>
        <p>Created at: ${new Date(group.created_at).toLocaleString()}</p>
        <p>Members: ${group.members.map(m => m.username).join(', ')}</p>
      `;
      container.appendChild(div);
    });
  } catch (err) {
    console.error('Error loading groups:', err);
  }
}
