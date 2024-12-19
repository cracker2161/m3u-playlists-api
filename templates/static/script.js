// API টগল ফাংশন
document.getElementById('apiToggle').addEventListener('change', function() {
    fetch('/api/toggle', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('statusText').textContent = data.status ? 'Active' : 'Inactive';
            showNotification(data.status ? 'API Activated' : 'API Deactivated');
        } else {
            showNotification('Error: ' + (data.error || 'Unknown error'), 'error');
            this.checked = !this.checked;
        }
    })
    .catch(error => {
        showNotification('Error: ' + error, 'error');
        this.checked = !this.checked;
    });
});

// শিডিউল আপডেট ফাংশন
function updateSchedule() {
    const startTime = document.getElementById('startTime').value;
    const endTime = document.getElementById('endTime').value;

    if (!startTime || !endTime) {
        showNotification('Please select both start and end time', 'error');
        return;
    }

    fetch('/api/schedule', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            start_time: startTime,
            end_time: endTime
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Schedule updated successfully!');
        } else {
            showNotification('Failed to update schedule: ' + (data.error || 'Unknown error'), 'error');
        }
    })
    .catch(error => {
        showNotification('Error: ' + error, 'error');
    });
}

// URL কপি ফাংশন
function copyUrl() {
    const urlText = document.getElementById('playlistUrl').textContent;
    navigator.clipboard.writeText(urlText)
        .then(() => showNotification('URL copied to clipboard!'))
        .catch(err => showNotification('Failed to copy URL', 'error'));
}

// নোটিফিকেশন ফাংশন
function showNotification(message, type = 'success') {
    // যদি আগের নোটিফিকেশন থাকে তবে রিমুভ করে
    const existingNotification = document.querySelector('.notification');
    if (existingNotification) {
        existingNotification.remove();
    }

    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;

    document.body.appendChild(notification);

    // ৩ সেকেন্ড পর নোটিফিকেশন হাইড করে
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// পেজ লোড হওয়ার সময় ইনিশিয়াল স্টেটাস চেক
document.addEventListener('DOMContentLoaded', function() {
    const toggle = document.getElementById('apiToggle');
    const statusText = document.getElementById('statusText');

    statusText.textContent = toggle.checked ? 'Active' : 'Inactive';
});