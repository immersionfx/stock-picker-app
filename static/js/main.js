/**
 * Main JavaScript for Stock Picker App
 */

document.addEventListener('DOMContentLoaded', function() {
    // Tab functionality
    initializeTabs();
    
    // Form submission with AJAX
    initializeFormSubmission();
    
    // Responsive sidebar toggle
    initializeSidebarToggle();
});

/**
 * Initialize tab functionality across the app
 */
function initializeTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // Remove active class from all buttons and panes
            tabBtns.forEach(b => b.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active'));
            
            // Add active class to clicked button and corresponding pane
            this.classList.add('active');
            const tabId = this.dataset.tab;
            const tabPane = document.getElementById(tabId);
            if (tabPane) {
                tabPane.classList.add('active');
            }
        });
    });
}

/**
 * Initialize form submission with AJAX
 */
function initializeFormSubmission() {
    const scanForm = document.getElementById('scan-form');
    if (scanForm) {
        scanForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Show loading indicator
            const submitBtn = scanForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.textContent = 'Scanning...';
            submitBtn.disabled = true;
            
            const formData = new FormData(scanForm);
            
            fetch(scanForm.action, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.href = data.redirect;
                } else {
                    alert('Error running scan. Please try again.');
                    submitBtn.textContent = originalText;
                    submitBtn.disabled = false;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error running scan. Please try again.');
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            });
        });
    }
}

/**
 * Initialize sidebar toggle for mobile view
 */
function initializeSidebarToggle() {
    // Add mobile sidebar toggle functionality if needed
    const sidebarToggle = document.createElement('button');
    sidebarToggle.className = 'sidebar-toggle';
    sidebarToggle.innerHTML = '<i class="fas fa-bars"></i>';
    
    const header = document.querySelector('header .container');
    if (header && window.innerWidth < 992) {
        header.prepend(sidebarToggle);
        
        sidebarToggle.addEventListener('click', function() {
            const sidebar = document.querySelector('.sidebar');
            sidebar.classList.toggle('active');
        });
    }
}

/**
 * Format large numbers with K, M, B suffixes
 * @param {number} num - Number to format
 * @returns {string} Formatted number
 */
function formatLargeNumber(num) {
    if (num >= 1e9) {
        return (num / 1e9).toFixed(2) + 'B';
    } else if (num >= 1e6) {
        return (num / 1e6).toFixed(2) + 'M';
    } else if (num >= 1e3) {
        return (num / 1e3).toFixed(2) + 'K';
    } else {
        return num.toFixed(2);
    }
}

/**
 * Update the current date/time in the footer
 */
function updateDateTime() {
    const dateTimeElement = document.getElementById('current-datetime');
    if (dateTimeElement) {
        const now = new Date();
        dateTimeElement.textContent = now.toLocaleString();
    }
}

// Update date/time every minute
setInterval(updateDateTime, 60000);
updateDateTime();