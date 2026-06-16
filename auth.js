// auth.js — shared authentication, user widget & balance modal logic

async function initAuth() {
    try {
        const res = await fetch('/api/user');
        if (res.status === 401) {
            window.location.href = '/login.html';
            return null;
        }
        const user = await res.json();
        _applyUser(user);
        return user;
    } catch {
        window.location.href = '/login.html';
        return null;
    }
}

function _applyUser(user) {
    const av = document.getElementById('uw-avatar');
    const nm = document.getElementById('uw-name');
    const bl = document.getElementById('uw-balance');
    if (av) av.textContent = user.username[0].toUpperCase();
    if (nm) nm.textContent = user.username;
    if (bl) bl.textContent = '💰 ' + parseFloat(user.balance).toFixed(2) + '$';
}

function refreshBalance(newBalance) {
    const bl = document.getElementById('uw-balance');
    if (bl) bl.textContent = '💰 ' + parseFloat(newBalance).toFixed(2) + '$';
}

function toggleUserMenu() {
    document.getElementById('uw-menu').classList.toggle('open');
}

// Close dropdown when clicking outside
document.addEventListener('click', e => {
    const widget = document.getElementById('user-widget');
    const menu   = document.getElementById('uw-menu');
    if (widget && menu && !widget.contains(e.target)) {
        menu.classList.remove('open');
    }
});

async function doLogout() {
    await fetch('/api/logout', { method: 'POST' });
    window.location.href = '/login.html';
}

// ── Balance Modal ──────────────────────────────────────────────────────────

function openBalanceModal() {
    const menu = document.getElementById('uw-menu');
    if (menu) menu.classList.remove('open');
    document.getElementById('balance-modal').style.display   = 'block';
    document.getElementById('balance-overlay').style.display = 'block';
    const inp = document.getElementById('balance-amount');
    if (inp) { inp.value = ''; inp.focus(); }
}

function closeBalanceModal() {
    document.getElementById('balance-modal').style.display   = 'none';
    document.getElementById('balance-overlay').style.display = 'none';
}

function setQuickAmount(n) {
    document.getElementById('balance-amount').value = n;
    document.getElementById('balance-amount').focus();
}

async function submitBalance() {
    const amount = parseFloat(document.getElementById('balance-amount').value);
    if (!amount || amount <= 0) { showToast('Enter a valid amount', 'error'); return; }

    const res  = await fetch('/api/balance/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount })
    });
    const data = await res.json();

    if (data.success) {
        refreshBalance(data.balance);
        closeBalanceModal();
        showToast(`+${amount.toFixed(2)}$ added to your account!`, 'success');
    } else {
        showToast(data.error || 'Something went wrong', 'error');
    }
}

// ── Toast ──────────────────────────────────────────────────────────────────

function showToast(msg, type = 'success') {
    let t = document.getElementById('_toast');
    if (!t) {
        t = document.createElement('div');
        t.id = '_toast';
        Object.assign(t.style, {
            position:    'fixed',
            bottom:      '30px',
            left:        '50%',
            transform:   'translateX(-50%) translateY(10px)',
            padding:     '14px 28px',
            borderRadius:'12px',
            fontFamily:  "'Poppins', sans-serif",
            fontSize:    '14px',
            fontWeight:  '600',
            color:       'white',
            zIndex:      '9999',
            opacity:     '0',
            transition:  'opacity 0.3s ease, transform 0.3s ease',
            whiteSpace:  'nowrap',
            boxShadow:   '0 8px 24px rgba(0,0,0,0.2)',
            pointerEvents: 'none'
        });
        document.body.appendChild(t);
    }
    t.textContent = msg;
    t.style.background = type === 'success'
        ? 'linear-gradient(135deg, #10b981, #059669)'
        : 'linear-gradient(135deg, #ef4444, #dc2626)';
    t.style.opacity   = '1';
    t.style.transform = 'translateX(-50%) translateY(0)';
    clearTimeout(t._tid);
    t._tid = setTimeout(() => {
        t.style.opacity   = '0';
        t.style.transform = 'translateX(-50%) translateY(10px)';
    }, 3200);
}
