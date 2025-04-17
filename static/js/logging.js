// WebSocket connection for real-time logging
let logSocket = null;
let logPopup = null;

function initLogging() {
    // Create WebSocket connection using port 8765
    logSocket = new WebSocket('ws://localhost:8765/ws/logs');
    
    // Create popup if it doesn't exist
    if (!logPopup) {
        createLogPopup();
    }

    // Check if log window should be visible
    if (localStorage.getItem('logWindowVisible') === 'true') {
        showLogPopup();
    }

    logSocket.onmessage = function(event) {
        const logMessage = JSON.parse(event.data);
        appendLogMessage(logMessage);
        console.log('Received log:', logMessage); // Debug logging
    };

    logSocket.onopen = function() {
        console.log('WebSocket connection established'); // Debug logging
    };

    logSocket.onerror = function(error) {
        console.error('WebSocket error:', error);
    };

    logSocket.onclose = function() {
        console.log('WebSocket connection closed'); // Debug logging
        // Try to reconnect after a delay
        setTimeout(initLogging, 3000);
    };
}

function showLogPopup() {
    if (!logPopup) {
        createLogPopup();
    }
    logPopup.style.display = 'flex';
    localStorage.setItem('logWindowVisible', 'true');
    
    // Clear previous logs only if not preserving them
    if (!localStorage.getItem('preserveLogs')) {
        const content = document.getElementById('log-content');
        if (content) {
            content.innerHTML = '';
        }
    }
}

function hideLogPopup() {
    if (logPopup) {
        logPopup.style.display = 'none';
        localStorage.setItem('logWindowVisible', 'false');
    }
}

function createLogPopup() {
    // Create popup container
    logPopup = document.createElement('div');
    logPopup.id = 'log-popup';
    logPopup.className = 'log-popup';
    logPopup.style.display = 'none'; // Hidden by default
    
    // Create header
    const header = document.createElement('div');
    header.className = 'log-popup-header';
    header.textContent = 'Application Logs';
    
    // Create log content area
    const content = document.createElement('div');
    content.className = 'log-popup-content';
    content.id = 'log-content';
    
    // Create close button
    const closeButton = document.createElement('button');
    closeButton.className = 'log-popup-close';
    closeButton.textContent = 'Close';
    closeButton.onclick = hideLogPopup;
    
    // Create clear button
    const clearButton = document.createElement('button');
    clearButton.className = 'log-popup-clear';
    clearButton.textContent = 'Clear Logs';
    clearButton.onclick = function() {
        const content = document.getElementById('log-content');
        if (content) {
            content.innerHTML = '';
        }
    };
    
    // Create button container
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'log-popup-buttons';
    buttonContainer.appendChild(clearButton);
    buttonContainer.appendChild(closeButton);
    
    // Assemble popup
    logPopup.appendChild(header);
    logPopup.appendChild(content);
    logPopup.appendChild(buttonContainer);
    
    // Add to document
    document.body.appendChild(logPopup);
    
    // Restore previous logs if they exist
    const savedLogs = localStorage.getItem('savedLogs');
    if (savedLogs) {
        content.innerHTML = savedLogs;
        content.scrollTop = content.scrollHeight;
    }
}

function appendLogMessage(logMessage) {
    const content = document.getElementById('log-content');
    if (!content) return;
    
    // Check if this message is a duplicate of the last message
    const lastLogEntry = content.lastElementChild;
    if (lastLogEntry) {
        const lastMessage = lastLogEntry.querySelector('.log-message').textContent;
        const lastLevel = lastLogEntry.querySelector('.log-level').textContent;
        
        // If message and level are the same as the last entry, skip adding it
        if (lastMessage === logMessage.message && lastLevel === logMessage.level) {
            return;
        }
    }
    
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry log-${logMessage.level.toLowerCase()}`;
    
    const timestamp = document.createElement('span');
    timestamp.className = 'log-timestamp';
    timestamp.textContent = new Date(logMessage.timestamp).toLocaleTimeString();
    
    const level = document.createElement('span');
    level.className = 'log-level';
    level.textContent = logMessage.level;
    
    const message = document.createElement('span');
    message.className = 'log-message';
    message.textContent = logMessage.message;
    
    logEntry.appendChild(timestamp);
    logEntry.appendChild(level);
    logEntry.appendChild(message);
    
    content.appendChild(logEntry);
    content.scrollTop = content.scrollHeight;
    
    // Save logs to localStorage
    localStorage.setItem('savedLogs', content.innerHTML);
}

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', function() {
    initLogging();
    
    // Add event listener to scan form
    const scanForm = document.getElementById('scan-form');
    if (scanForm) {
        scanForm.addEventListener('submit', function(e) {
            // Show the log popup
            showLogPopup();
            localStorage.setItem('preserveLogs', 'true');
            
            // Submit the form using fetch to prevent page reload
            e.preventDefault();
            
            fetch('/run_scan', {
                method: 'POST',
                body: new FormData(this)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success && data.redirect) {
                    // Reload the page content without closing the log popup
                    window.location.href = data.redirect;
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    }
    
    // Add event listener for the "Show Logs" button in nav
    const showLogsButton = document.querySelector('a[onclick="document.getElementById(\'log-popup\').style.display=\'block\'"]');
    if (showLogsButton) {
        showLogsButton.onclick = function(e) {
            e.preventDefault();
            showLogPopup();
        };
    }
}); 