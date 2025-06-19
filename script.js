// Amazon Seva Pay - Complete JavaScript Functionality

// Global variables
let offlineTransactions = [];
let isOnline = navigator.onLine;
let currentUser = null;
let ambassadorEarnings = 0;

// Initialize app when DOM loads
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    loadOfflineData();
    updateConnectionStatus();
});

// Initialize application
function initializeApp() {
    console.log('Amazon Seva Pay - Initializing...');
    
    // Load saved data from localStorage
    loadOfflineData();
    
    // Set up connection status monitoring
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    // Initialize QR code library if available
    if (typeof QRCode !== 'undefined') {
        console.log('QR Code library loaded');
    }
}

// Set up event listeners
function setupEventListeners() {
    // Customer page events
    const generateQRBtn = document.getElementById('generateQR');
    if (generateQRBtn) {
        generateQRBtn.addEventListener('click', generateQRCode);
    }
    
    const orderForm = document.getElementById('orderForm');
    if (orderForm) {
        orderForm.addEventListener('submit', handleOrderSubmission);
    }
    
    // Ambassador page events
    const scanQRBtn = document.getElementById('scanQR');
    if (scanQRBtn) {
        scanQRBtn.addEventListener('click', scanQRCode);
    }
    
    const processPaymentBtn = document.getElementById('processPayment');
    if (processPaymentBtn) {
        processPaymentBtn.addEventListener('click', processPayment);
    }
    
    const syncBtn = document.getElementById('syncTransactions');
    if (syncBtn) {
        syncBtn.addEventListener('click', syncOfflineTransactions);
    }
}

// Connection status handlers
function handleOnline() {
    isOnline = true;
    updateConnectionStatus();
    showAlert('Connection restored! Syncing transactions...', 'success');
    syncOfflineTransactions();
}

function handleOffline() {
    isOnline = false;
    updateConnectionStatus();
    showAlert('Offline mode activated. Transactions will be saved locally.', 'info');
}

function updateConnectionStatus() {
    const statusElements = document.querySelectorAll('.connection-status');
    statusElements.forEach(element => {
        if (isOnline) {
            element.textContent = '🟢 Online';
            element.className = 'status status-online';
        } else {
            element.textContent = '🔴 Offline';
            element.className = 'status status-offline';
        }
    });
}

// Customer Functions
function generateQRCode() {
    const productName = document.getElementById('productName')?.value;
    const amount = document.getElementById('amount')?.value;
    const customerName = document.getElementById('customerName')?.value;
    const customerPhone = document.getElementById('customerPhone')?.value;
    
    if (!productName || !amount || !customerName || !customerPhone) {
        showAlert('Please fill all fields', 'error');
        return;
    }
    
    // Create transaction data
    const transactionData = {
        id: generateTransactionId(),
        productName: productName,
        amount: parseFloat(amount),
        customerName: customerName,
        customerPhone: customerPhone,
        timestamp: new Date().toISOString(),
        status: 'pending'
    };
    
    // Generate QR code data
    const qrData = JSON.stringify(transactionData);
    
    // Display QR code
    displayQRCode(qrData);
    
    // Store transaction locally
    storeTransactionLocally(transactionData);
    
    // Show success message
    showAlert('QR Code generated successfully! Show this to your Payment Ambassador.', 'success');
}

function displayQRCode(data) {
    const qrDisplay = document.getElementById('qrDisplay');
    const qrCodeElement = document.getElementById('qrcode');
    
    if (qrDisplay && qrCodeElement) {
        // Clear previous QR code
        qrCodeElement.innerHTML = '';
        
        // Generate new QR code
        if (typeof QRCode !== 'undefined') {
            new QRCode(qrCodeElement, {
                text: data,
                width: 200,
                height: 200,
                colorDark: "#232f3e",
                colorLight: "#ffffff"
            });
        } else {
            // Fallback: display data as text
            qrCodeElement.innerHTML = `
                <div style="padding: 20px; border: 2px solid #232f3e; background: white; font-family: monospace; word-break: break-all;">
                    <strong>QR Data:</strong><br>
                    ${data}
                </div>
            `;
        }
        
        qrDisplay.style.display = 'block';
        qrDisplay.classList.add('fade-in');
    }
}

function handleOrderSubmission(event) {
    event.preventDefault();
    generateQRCode();
}

// Ambassador Functions
function scanQRCode() {
    // Simulate QR code scanning (in real app, this would use camera)
    const mockQRData = {
        id: generateTransactionId(),
        productName: "Sample Product",
        amount: 299,
        customerName: "John Doe",
        customerPhone: "9876543210",
        timestamp: new Date().toISOString(),
        status: 'pending'
    };
    
    displayTransactionDetails(mockQRData);
    
    // In real implementation, you would integrate with camera API
    showAlert('QR Code scanned successfully!', 'success');
}

function displayTransactionDetails(transactionData) {
    const transactionDisplay = document.getElementById('transactionDetails');
    
    if (transactionDisplay) {
        transactionDisplay.innerHTML = `
            <div class="transaction fade-in">
                <h3>Transaction Details</h3>
                <div class="transaction-details">
                    <div class="transaction-item">
                        <span class="transaction-label">Transaction ID:</span>
                        <span class="transaction-value">${transactionData.id}</span>
                    </div>
                    <div class="transaction-item">
                        <span class="transaction-label">Product:</span>
                        <span class="transaction-value">${transactionData.productName}</span>
                    </div>
                    <div class="transaction-item">
                        <span class="transaction-label">Amount:</span>
                        <span class="transaction-value">₹${transactionData.amount}</span>
                    </div>
                    <div class="transaction-item">
                        <span class="transaction-label">Customer:</span>
                        <span class="transaction-value">${transactionData.customerName}</span>
                    </div>
                    <div class="transaction-item">
                        <span class="transaction-label">Phone:</span>
                        <span class="transaction-value">${transactionData.customerPhone}</span>
                    </div>
                    <div class="transaction-item">
                        <span class="transaction-label">Time:</span>
                        <span class="transaction-value">${new Date(transactionData.timestamp).toLocaleString()}</span>
                    </div>
                </div>
                <button id="confirmPayment" class="btn btn-secondary" onclick="processPayment('${transactionData.id}')">
                    Confirm Cash Payment Received
                </button>
            </div>
        `;
        
        // Store transaction for processing
        window.currentTransaction = transactionData;
    }
}

function processPayment(transactionId) {
    if (!window.currentTransaction) {
        showAlert('No transaction to process', 'error');
        return;
    }
    
    // Calculate commission (2% of transaction amount)
    const commission = window.currentTransaction.amount * 0.02;
    
    // Update transaction status
    window.currentTransaction.status = 'completed';
    window.currentTransaction.processedAt = new Date().toISOString();
    window.currentTransaction.commission = commission;
    
    // Add to offline transactions
    offlineTransactions.push(window.currentTransaction);
    
    // Update ambassador earnings
    ambassadorEarnings += commission;
    updateEarningsDisplay();
    
    // Save to local storage
    saveOfflineData();
    
    // Show success message
    showAlert(`Payment processed successfully! Commission earned: ₹${commission.toFixed(2)}`, 'success');
    
    // Clear transaction display
    const transactionDisplay = document.getElementById('transactionDetails');
    if (transactionDisplay) {
        transactionDisplay.innerHTML = '<p>Ready to scan next QR code...</p>';
    }
    
    // Sync if online
    if (isOnline) {
        setTimeout(syncOfflineTransactions, 1000);
    }
    
    // Clear current transaction
    window.currentTransaction = null;
}

function updateEarningsDisplay() {
    const earningsElement = document.getElementById('totalEarnings');
    if (earningsElement) {
        earningsElement.textContent = `₹${ambassadorEarnings.toFixed(2)}`;
    }
    
    const transactionCountElement = document.getElementById('transactionCount');
    if (transactionCountElement) {
        transactionCountElement.textContent = offlineTransactions.length;
    }
}

// Offline Data Management
function storeTransactionLocally(transaction) {
    let localTransactions = JSON.parse(localStorage.getItem('sevaPayTransactions') || '[]');
    localTransactions.push(transaction);
    localStorage.setItem('sevaPayTransactions', JSON.stringify(localTransactions));
}

function loadOfflineData() {
    // Load transactions
    const savedTransactions = localStorage.getItem('sevaPayTransactions');
    if (savedTransactions) {
        offlineTransactions = JSON.parse(savedTransactions);
    }
    
    // Load earnings
    const savedEarnings = localStorage.getItem('sevaPayEarnings');
    if (savedEarnings) {
        ambassadorEarnings = parseFloat(savedEarnings);
        updateEarningsDisplay();
    }
}

function saveOfflineData() {
    localStorage.setItem('sevaPayTransactions', JSON.stringify(offlineTransactions));
    localStorage.setItem('sevaPayEarnings', ambassadorEarnings.toString());
}

function syncOfflineTransactions() {
    if (!isOnline) {
        showAlert('Cannot sync - device is offline', 'error');
        return;
    }
    
    if (offlineTransactions.length === 0) {
        showAlert('No transactions to sync', 'info');
        return;
    }
    
    // Show loading spinner
    showLoadingSpinner();
    
    // Simulate API call to sync transactions
    setTimeout(() => {
        // In real implementation, this would be an actual API call
        console.log('Syncing transactions:', offlineTransactions);
        
        // Mark transactions as synced
        offlineTransactions.forEach(transaction => {
            transaction.synced = true;
        });
        
        // Save updated data
        saveOfflineData();
        
        // Hide loading spinner
        hideLoadingSpinner();
        
        // Show success message
        showAlert(`Successfully synced ${offlineTransactions.length} transactions!`, 'success');
        
    }, 2000); // 2 second delay to simulate network request
}

// Utility Functions
function generateTransactionId() {
    return 'SP' + Date.now() + Math.random().toString(36).substr(2, 5).toUpperCase();
}

function showAlert(message, type = 'info') {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.alert');
    existingAlerts.forEach(alert => alert.remove());
    
    // Create new alert
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} fade-in`;
    alert.textContent = message;
    
    // Insert at top of main content
    const mainContent = document.querySelector('.main-content') || document.body;
    mainContent.insertBefore(alert, mainContent.firstChild);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 5000);
}

function showLoadingSpinner() {
    const spinner = document.createElement('div');
    spinner.id = 'loadingSpinner';
    spinner.className = 'spinner';
    
    const mainContent = document.querySelector('.main-content') || document.body;
    mainContent.appendChild(spinner);
}

function hideLoadingSpinner() {
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) {
        spinner.remove();
    }
}

// Demo Functions (for presentation)
function runDemo() {
    showAlert('Starting Amazon Seva Pay Demo...', 'info');
    
    setTimeout(() => {
        if (window.location.pathname.includes('customer')) {
            demoCustomerFlow();
        } else if (window.location.pathname.includes('ambassador')) {
            demoAmbassadorFlow();
        }
    }, 1000);
}

function demoCustomerFlow() {
    // Auto-fill form
    const productName = document.getElementById('productName');
    const amount = document.getElementById('amount');
    const customerName = document.getElementById('customerName');
    const customerPhone = document.getElementById('customerPhone');
    
    if (productName) productName.value = 'Amazon Echo Dot';
    if (amount) amount.value = '2999';
    if (customerName) customerName.value = 'Priya Sharma';
    if (customerPhone) customerPhone.value = '9876543210';
    
    setTimeout(() => {
        generateQRCode();
    }, 1000);
}

function demoAmbassadorFlow() {
    setTimeout(() => {
        scanQRCode();
    }, 500);
    
    setTimeout(() => {
        if (document.getElementById('confirmPayment')) {
            document.getElementById('confirmPayment').click();
        }
    }, 2000);
}

// Export functions for global access
window.SevaPayApp = {
    generateQRCode,
    scanQRCode,
    processPayment,
    syncOfflineTransactions,
    runDemo,
    showAlert
};

console.log('Amazon Seva Pay - JavaScript loaded successfully!');
