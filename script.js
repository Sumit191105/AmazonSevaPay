<script src="https://cdnjs.cloudflare.com/ajax/libs/qrious/4.0.2/qrious.min.js"></script>
<script>
  const secretKey = "seva123";
  let transactions = JSON.parse(localStorage.getItem("transactions") || "[]");
  let ambEarnings = 0;
  let ambTodayEarnings = 0;
  let ambTxCount = 0;
  let ambTxList = [];
  document.getElementById('download-today-report').onclick = function() {
      let allTx = [];
      try {
        allTx = JSON.parse(localStorage.getItem("transactions") || "[]");
      } catch { allTx = []; }
    
      // Get today's date string
      const todayStr = new Date().toLocaleDateString();
    
      // Group earnings by ambassador for today
      const earningsToday = {};
      allTx.forEach(tx => {
        const ambassador = tx.ambassador || "Ambassador 1";
        const txDate = new Date(tx.time).toLocaleDateString();
        if (txDate === todayStr) {
          if (!earningsToday[ambassador]) earningsToday[ambassador] = 0;
          earningsToday[ambassador] += parseFloat(tx.commission || 0);
        }
      });
    
      // Build CSV
      let csv = "Ambassador,Today's Earnings (₹)\n";
      Object.keys(earningsToday).forEach(amb => {
        csv += `${amb},${earningsToday[amb].toFixed(2)}\n`;
      });
      if (Object.keys(earningsToday).length === 0) {
        csv += "No earnings today,0\n";
      }
    
      // Download as CSV
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `amazon-seva-pay-today-earnings-${todayStr.replace(/\//g,'-')}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    };
    
  function showTab(tabId) {
    document.querySelectorAll('.tab-buttons button').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
    document.querySelector(`[onclick="showTab('${tabId}')"]`).classList.add('active');
    document.getElementById(tabId).classList.add('active');
    if (tabId === 'admin') renderAdminEarningsTable();
    if (tabId === 'ambassador') updateAmbDashboard();
  }
  function chooseRole(role) {
    document.getElementById('roleModal').style.display = 'none';
    document.getElementById('popupModal').style.display = 'block';
    showTab(role);
  }
  function generateQR() {
    const name = document.getElementById("name").value.trim();
    const phone = document.getElementById("phone").value.trim();
    const product = document.getElementById("product").value.trim();
    const amount = document.getElementById("amount").value.trim();
    if (!name || !phone || !product || !amount) {
      alert("Please fill all fields");
      return;
    }
    const data = `${name}|${phone}|${product}|${amount}`;
    const signature = btoa(data + secretKey);
    const qrObj = { name, phone, product, amount, signature };
    new QRious({
      element: document.getElementById("qr-canvas"),
      value: JSON.stringify(qrObj),
      size: 200
    });
    document.getElementById("qr-json").innerText = JSON.stringify(qrObj);
  }
  function processQRData() {
    const qrData = document.getElementById("qrdata").value.trim();
    const ambassador = document.getElementById("ambassadorName").value.trim() || "Ambassador 1";
    if (!qrData) {
      alert("Please paste QR data");
      return;
    }
    try {
      const tx = JSON.parse(qrData);
      const verifySig = btoa(`${tx.name}|${tx.phone}|${tx.product}|${tx.amount}` + secretKey);
      if (tx.signature === verifySig) {
        // Save with ambassador and commission info
        const commission = parseFloat(tx.amount) * 0.02;
        const txObj = {
          ambassador,
          name: tx.name,
          phone: tx.phone,
          product: tx.product,
          amount: tx.amount,
          commission,
          time: new Date().toLocaleString()
        };
        transactions.push(txObj);
        localStorage.setItem("transactions", JSON.stringify(transactions));
        alert("Transaction Stored Offline");
        document.getElementById("qrdata").value = "";
        displayTransactions();
        updateAmbDashboard();
      } else {
        alert("Invalid Signature - Fraud suspected");
      }
    } catch {
      alert("Invalid QR data");
    }
  }
  function syncTransactions() {
    if (!navigator.onLine) {
      alert("No Internet Connection");
      return;
    }
    const txDiv = document.getElementById("transactions");
    txDiv.innerHTML = "";
    transactions.forEach(tx => {
      txDiv.innerHTML += `<div class='transaction-item'>
        Order from ${tx.name} for ₹${tx.amount} - Synced ✅<br/>
        Commission Earned: ₹${parseFloat(tx.commission).toFixed(2)}
      </div>`;
    });
    localStorage.removeItem("transactions");
    transactions = [];
    updateAmbDashboard();
  }
  function displayTransactions() {
    const txDiv = document.getElementById("transactions");
    txDiv.innerHTML = "";
    transactions.forEach(tx => {
      txDiv.innerHTML += `<div class='transaction-item'>
        Order from ${tx.name} for ₹${tx.amount} - Pending
      </div>`;
    });
  }
  // Ambassador Dashboard Logic
  function updateAmbDashboard() {
    const ambassador = document.getElementById("ambassadorName") ? (document.getElementById("ambassadorName").value.trim() || "Ambassador 1") : "Ambassador 1";
    // Filter transactions for this ambassador
    const now = new Date();
    ambTxList = transactions.filter(tx => tx.ambassador === ambassador);
    ambEarnings = ambTxList.reduce((sum, tx) => sum + (parseFloat(tx.commission) || 0), 0);
    ambTodayEarnings = ambTxList.filter(tx => {
      const txDate = new Date(tx.time);
      return txDate.toDateString() === now.toDateString();
    }).reduce((sum, tx) => sum + (parseFloat(tx.commission) || 0), 0);
    ambTxCount = ambTxList.length;
    document.getElementById('amb-total-earnings').textContent = ambEarnings.toFixed(2);
    document.getElementById('amb-today-earnings').textContent = ambTodayEarnings.toFixed(2);
    document.getElementById('amb-total-tx').textContent = ambTxCount;
    renderAmbTxList();
  }
  function renderAmbTxList() {
    const txDiv = document.getElementById('amb-tx-list');
    if (!ambTxList.length) {
      txDiv.innerHTML = "<div style='color:#888; text-align:center;'>No transactions yet</div>";
      return;
    }
    txDiv.innerHTML = ambTxList.slice(0,10).map(tx => `
      <div class="transaction-item" style="border-left:4px solid #f0c14b;">
        <div><b>${tx.name}</b> • ₹${tx.amount} <span style="color:#888; font-size:0.95em;">(${tx.product})</span></div>
        <div style="font-size:0.95em; color:#666;">${tx.time}</div>
        <div style="font-size:0.95em; color:#28a745;">Commission: ₹${parseFloat(tx.commission).toFixed(2)}</div>
      </div>
    `).join('');
  }
  // Ambassador Mode: Simulate QR Scan
  function simulateQRScan() {
    const ambassador = document.getElementById("ambassadorName") ? (document.getElementById("ambassadorName").value.trim() || "Ambassador 1") : "Ambassador 1";
    const customer = "Customer " + (Math.floor(Math.random()*900)+100);
    const product = "P" + (Math.floor(Math.random()*9000)+1000);
    const amount = Math.floor(Math.random()*400)+100;
    const commission = amount * 0.02;
    const tx = {
      ambassador,
      name: customer,
      product,
      amount,
      commission,
      time: new Date().toLocaleString()
    };
    transactions.push(tx);
    localStorage.setItem("transactions", JSON.stringify(transactions));
    updateAmbDashboard();
    ambNotify(`Payment processed: ₹${amount} (Commission: ₹${commission.toFixed(2)})`);
  }
  // Manual Entry Toggle
  function toggleManualEntry() {
    const form = document.getElementById('manualEntryForm');
    form.style.display = form.style.display === "none" ? "block" : "none";
  }
  // Manual Payment
  function processManualPayment() {
    const ambassador = document.getElementById("ambassadorName") ? (document.getElementById("ambassadorName").value.trim() || "Ambassador 1") : "Ambassador 1";
    const customer = document.getElementById('manualCustomer').value.trim();
    const product = document.getElementById('manualProduct').value.trim();
    const amount = parseFloat(document.getElementById('manualAmount').value);
    if (!customer || !amount || amount <= 0 || !product) {
      ambNotify("Please enter valid customer, product, and amount", true);
      return;
    }
    const commission = amount * 0.02;
    const tx = {
      ambassador,
      name: customer,
      product,
      amount,
      commission,
      time: new Date().toLocaleString()
    };
    transactions.push(tx);
    localStorage.setItem("transactions", JSON.stringify(transactions));
    updateAmbDashboard();
    ambNotify(`Payment processed: ₹${amount} (Commission: ₹${commission.toFixed(2)})`);
    document.getElementById('manualCustomer').value = "";
    document.getElementById('manualProduct').value = "";
    document.getElementById('manualAmount').value = "";
    document.getElementById('manualEntryForm').style.display = "none";
  }
  // Amazon-Style Notification
  function ambNotify(msg, error) {
    const n = document.getElementById('amb-notify');
    n.textContent = msg;
    n.style.background = error ? "#b12704" : "#232f3e";
    n.style.display = "block";
    setTimeout(()=>{ n.style.display="none"; }, 2500);
  }
  // Admin Dashboard: Earnings by Ambassador and Product ID
  function renderAdminEarningsTable() {
    let allTx = [];
    try {
      allTx = JSON.parse(localStorage.getItem("transactions") || "[]");
    } catch { allTx = []; }
    // Group by ambassador and product
    const earningsMap = {};
    allTx.forEach(tx => {
      const ambassador = tx.ambassador || "Ambassador 1";
      const product = tx.product || tx.productId || "Unknown";
      const commission = parseFloat(tx.commission || 3);
      if (!earningsMap[ambassador]) earningsMap[ambassador] = {};
      if (!earningsMap[ambassador][product]) earningsMap[ambassador][product] = 0;
      earningsMap[ambassador][product] += commission;
    });
    // Build table HTML
    let html = `<table class="admin-table">
      <tr>
        <th>Ambassador</th>
        <th>Product ID</th>
        <th>Total Earnings (₹)</th>
      </tr>`;
    let found = false;
    Object.keys(earningsMap).forEach(amb => {
      Object.keys(earningsMap[amb]).forEach(prod => {
        found = true;
        html += `<tr>
          <td>${amb}</td>
          <td>${prod}</td>
          <td>₹${earningsMap[amb][prod].toFixed(2)}</td>
        </tr>`;
      });
    });
    if (!found) {
      html += `<tr><td colspan="3" style="text-align:center; color:#888;">No earnings data available</td></tr>`;
    }
    html += `</table>`;
    document.getElementById('admin-earnings-table').innerHTML = html;
  }
  // Display pending transactions on load
  window.onload = displayTransactions;
</script>
