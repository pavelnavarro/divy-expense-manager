// static/js/groups.js

document.addEventListener('DOMContentLoaded', () => {
    const createBtn      = document.getElementById('createGroupBtn');
    const modal          = document.getElementById('createGroupModal');
    const closeModalBtn  = document.getElementById('closeGroupModal');
    const form           = document.getElementById('createGroupForm');
    const membersSelect  = document.getElementById('members');
    const groupsList     = document.getElementById('groupsList');
  
    // 1) Modal open/close
    createBtn.addEventListener('click', () => modal.style.display = 'block');
    closeModalBtn.addEventListener('click', () => modal.style.display = 'none');
    window.addEventListener('click', e => {
      if (e.target === modal) modal.style.display = 'none';
    });
  
    // 2) Load possible members
    async function loadMembers() {
      try {
        const res = await fetch('/api/shared/users');
        const users = await res.json();
        users.forEach(u => {
          const opt = new Option(u.username, u.id);
          membersSelect.add(opt);
        });
      } catch (err) {
        console.error('Could not load users', err);
      }
    }
  
    // 3) Load existing groups
    async function loadGroups() {
      groupsList.innerHTML = 'Loading...';
      try {
        const res = await fetch('/api/shared/groups');
        const groups = await res.json();
        if (!groups.length) {
          groupsList.innerHTML = '<p>You’re not in any groups yet.</p>';
          return;
        }
        groupsList.innerHTML = groups.map(g => `
          <div class="group-card">
            <h4>${g.name}</h4>
            <p>Created At: ${new Date(g.created_at).toLocaleDateString()}</p>
            <p>Members: ${g.members.map(m=>m.username).join(', ')}</p>
            <a href="/groups/${g.id}">Details</a>
          </div>
        `).join('');
      } catch (err) {
        groupsList.innerHTML = '<p>Error loading groups</p>';
        console.error(err);
      }
    }
  
    // 4) Handle create-group form submit
    form.addEventListener('submit', async e => {
      e.preventDefault();
      const name    = document.getElementById('groupName').value;
      const members = Array.from(membersSelect.selectedOptions).map(o => o.value);
  
      try {
        const res = await fetch('/api/shared/groups', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, members })
        });
        if (res.ok) {
          modal.style.display = 'none';
          form.reset();
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
  
    // init
    loadMembers();
    loadGroups();
  });
  