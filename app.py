from flask import Flask, render_template, request, jsonify, session
import sqlite3
import json
import hashlib
import time
import random
import string
import qrcode
import io
import base64
from datetime import datetime
from sync_manager import SevaPaySyncManager

app = Flask(__name__)
app.secret_key = 'seva_pay_secret_key_2025'

# Initialize Database
def init_db():
    conn = sqlite3.connect('seva_pay.db')
    cursor = conn.cursor()
    
    # Create customers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            email TEXT,
            location TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create ambassadors table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ambassadors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            business_name TEXT,
            location TEXT,
            total_earnings REAL DEFAULT 0.0,
            commission_rate REAL DEFAULT 0.02,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT UNIQUE NOT NULL,
            customer_id INTEGER,
            ambassador_id INTEGER,
            amount REAL NOT NULL,
            commission REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            offline_stored BOOLEAN DEFAULT 0,
            product_details TEXT,
            qr_code TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            synced_at TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers (id),
            FOREIGN KEY (ambassador_id) REFERENCES ambassadors (id)
        )
    ''')
    
    # Create offline_queue table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS offline_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            synced BOOLEAN DEFAULT 0
        )
    ''')
    
    # Insert sample data
    cursor.execute("SELECT COUNT(*) FROM customers")
    if cursor.fetchone()[0] == 0:
        # Sample customers
        sample_customers = [
            ('Priya Sharma', '9876543210', 'priya@gmail.com', 'Banda, UP'),
            ('Rahul Kumar', '9876543211', 'rahul@gmail.com', 'Varanasi, UP'),
            ('Sunita Devi', '9876543212', 'sunita@gmail.com', 'Allahabad, UP')
        ]
        cursor.executemany('''
            INSERT INTO customers (name, phone, email, location) VALUES (?, ?, ?, ?)
        ''', sample_customers)
        
        # Sample ambassadors
        sample_ambassadors = [
            ('Ravi Tea Stall', '9876543220', 'Ravi Chai Center', 'Banda, UP', 1250.50, 0.02),
            ('Maya General Store', '9876543221', 'Maya Kirana Store', 'Varanasi, UP', 2340.75, 0.02),
            ('Suresh Mobile Shop', '9876543222', 'Suresh Electronics', 'Allahabad, UP', 890.25, 0.02)
        ]
        cursor.executemany('''
            INSERT INTO ambassadors (name, phone, business_name, location, total_earnings, commission_rate) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', sample_ambassadors)
    
    conn.commit()
    conn.close()

# Initialize sync manager
sync_manager = SevaPaySyncManager()

# Utility functions
def generate_transaction_id():
    return 'SP' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def generate_qr_data(transaction_id, amount, product_details):
    qr_data = {
        'transaction_id': transaction_id,
        'amount': amount,
        'product': product_details,
        'timestamp': int(time.time()),
        'hash': hashlib.md5(f"{transaction_id}{amount}{time.time()}".encode()).hexdigest()[:8]
    }
    return json.dumps(qr_data)

def calculate_commission(amount, rate=0.02):
    return round(amount * rate, 2)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/customer')
def customer_dashboard():
    return render_template('customer.html')

@app.route('/ambassador')
def ambassador_dashboard():
    return render_template('ambassador.html')

@app.route('/demo')
def demo_page():
    return render_template('demo.html')

@app.route('/api/customer/login', methods=['POST'])
def customer_login():
    data = request.get_json()
    phone = data.get('phone')
    
    conn = sqlite3.connect('seva_pay.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM customers WHERE phone = ?', (phone,))
    customer = cursor.fetchone()
    conn.close()
    
    if customer:
        session['customer_id'] = customer[0]
        session['customer_name'] = customer[1]
        return jsonify({'success': True, 'customer': {'id': customer[0], 'name': customer[1], 'phone': customer[2]}})
    else:
        return jsonify({'success': False, 'message': 'Customer not found'})

@app.route('/api/ambassador/login', methods=['POST'])
def ambassador_login():
    data = request.get_json()
    phone = data.get('phone')
    
    conn = sqlite3.connect('seva_pay.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ambassadors WHERE phone = ?', (phone,))
    ambassador = cursor.fetchone()
    conn.close()
    
    if ambassador:
        session['ambassador_id'] = ambassador[0]
        session['ambassador_name'] = ambassador[1]
        return jsonify({
            'success': True, 
            'ambassador': {
                'id': ambassador[0], 
                'name': ambassador[1], 
                'business_name': ambassador[3],
                'total_earnings': ambassador[5]
            }
        })
    else:
        return jsonify({'success': False, 'message': 'Ambassador not found'})

@app.route('/api/generate-qr', methods=['POST'])
def generate_qr():
    data = request.get_json()
    amount = float(data.get('amount'))
    product_details = data.get('product_details', '')
    
    if 'customer_id' not in session:
        return jsonify({'success': False, 'message': 'Customer not logged in'})
    
    transaction_id = generate_transaction_id()
    qr_data = generate_qr_data(transaction_id, amount, product_details)
    
    # Store transaction as pending
    conn = sqlite3.connect('seva_pay.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transactions (transaction_id, customer_id, amount, commission, product_details, qr_code, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (transaction_id, session['customer_id'], amount, calculate_commission(amount), product_details, qr_data, 'pending'))
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'transaction_id': transaction_id,
        'qr_data': qr_data,
        'amount': amount,
        'product_details': product_details
    })

@app.route('/api/process-payment', methods=['POST'])
def process_payment():
    data = request.get_json()
    qr_data = json.loads(data.get('qr_data'))
    transaction_id = qr_data.get('transaction_id')
    cash_received = float(data.get('cash_received'))
    
    if 'ambassador_id' not in session:
        return jsonify({'success': False, 'message': 'Ambassador not logged in'})
    
    conn = sqlite3.connect('seva_pay.db')
    cursor = conn.cursor()
    
    # Get transaction details
    cursor.execute('SELECT * FROM transactions WHERE transaction_id = ?', (transaction_id,))
    transaction = cursor.fetchone()
    
    if not transaction:
        conn.close()
        return jsonify({'success': False, 'message': 'Transaction not found'})
    
    transaction_amount = transaction[3]
    commission = transaction[4]
    
    if cash_received < transaction_amount:
        conn.close()
        return jsonify({'success': False, 'message': 'Insufficient cash received'})
    
    # Update transaction
    cursor.execute('''
        UPDATE transactions 
        SET ambassador_id = ?, status = ?, offline_stored = ?, synced_at = CURRENT_TIMESTAMP
        WHERE transaction_id = ?
    ''', (session['ambassador_id'], 'completed', 1, transaction_id))
    
    # Update ambassador earnings
    cursor.execute('''
        UPDATE ambassadors 
        SET total_earnings = total_earnings + ?
        WHERE id = ?
    ''', (commission, session['ambassador_id']))
    
    conn.commit()
    conn.close()
    
    change = cash_received - transaction_amount
    
    return jsonify({
        'success': True,
        'transaction_id': transaction_id,
        'amount': transaction_amount,
        'commission': commission,
        'cash_received': cash_received,
        'change': change,
        'message': 'Payment processed successfully'
    })

@app.route('/api/transactions')
def get_transactions():
    conn = sqlite3.connect('seva_pay.db')
    cursor = conn.cursor()
    
    if 'customer_id' in session:
        cursor.execute('''
            SELECT t.transaction_id, t.amount, t.status, t.product_details, t.created_at,
                   a.business_name
            FROM transactions t
            LEFT JOIN ambassadors a ON t.ambassador_id = a.id
            WHERE t.customer_id = ?
            ORDER BY t.created_at DESC
        ''', (session['customer_id'],))
    elif 'ambassador_id' in session:
        cursor.execute('''
            SELECT t.transaction_id, t.amount, t.commission, t.status, t.product_details, t.created_at,
                   c.name as customer_name
            FROM transactions t
            LEFT JOIN customers c ON t.customer_id = c.id
            WHERE t.ambassador_id = ?
            ORDER BY t.created_at DESC
        ''', (session['ambassador_id'],))
    else:
        conn.close()
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    transactions = cursor.fetchall()
    conn.close()
    
    return jsonify({'success': True, 'transactions': transactions})

@app.route('/api/stats')
def get_stats():
    conn = sqlite3.connect('seva_pay.db')
    cursor = conn.cursor()
    
    # Overall stats
    cursor.execute('SELECT COUNT(*) FROM customers')
    total_customers = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM ambassadors WHERE status = "active"')
    active_ambassadors = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM transactions WHERE status = "completed"')
    completed_transactions = cursor.fetchone()[0]
    
    cursor.execute('SELECT SUM(amount) FROM transactions WHERE status = "completed"')
    total_volume = cursor.fetchone()[0] or 0
    
    cursor.execute('SELECT SUM(commission) FROM transactions WHERE status = "completed"')
    total_commission = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return jsonify({
        'success': True,
        'stats': {
            'total_customers': total_customers,
            'active_ambassadors': active_ambassadors,
            'completed_transactions': completed_transactions,
            'total_volume': round(total_volume, 2),
            'total_commission': round(total_commission, 2),
            'success_rate': round((completed_transactions / max(completed_transactions + 10, 1)) * 100, 1)
        }
    })

@app.route('/api/offline-sync', methods=['POST'])
def offline_sync():
    """Simulate offline transaction sync"""
    data = request.get_json()
    offline_transactions = data.get('transactions', [])
    
    conn = sqlite3.connect('seva_pay.db')
    cursor = conn.cursor()
    
    synced_count = 0
    for transaction in offline_transactions:
        try:
            cursor.execute('''
                INSERT INTO offline_queue (transaction_data, synced) VALUES (?, ?)
            ''', (json.dumps(transaction), 1))
            synced_count += 1
        except Exception as e:
            print(f"Error syncing transaction: {e}")
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'synced_count': synced_count,
        'message': f'Successfully synced {synced_count} offline transactions'
    })

@app.route('/api/network/toggle', methods=['POST'])
def toggle_network():
    """Toggle network status for demo purposes"""
    new_status = sync_manager.simulate_network_toggle()
    return jsonify({
        'success': True,
        'network_online': new_status,
        'message': f"Network is now {'Online' if new_status else 'Offline'}"
    })

@app.route('/api/network/status', methods=['GET'])
def get_network_status():
    """Get current network status"""
    status = sync_manager.get_network_status()
    return jsonify(status)

@app.route('/api/transaction/create', methods=['POST'])
def create_transaction():
    """Create a new offline transaction"""
    data = request.json
    
    required_fields = ['customer_id', 'ambassador_id', 'amount', 'product_name']
    if not all(field in data for field in required_fields):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    transaction_id = sync_manager.create_offline_transaction(
        data['customer_id'],
        data['ambassador_id'],
        float(data['amount']),
        data['product_name']
    )
    
    # Generate QR code for the transaction
    qr_data = {
        'transaction_id': transaction_id,
        'amount': data['amount'],
        'product': data['product_name'],
        'customer': data['customer_id']
    }
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(json.dumps(qr_data))
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return jsonify({
        'success': True,
        'transaction_id': transaction_id,
        'qr_code': f"data:image/png;base64,{qr_code_base64}",
        'message': 'Transaction created successfully'
    })

@app.route('/api/transaction/process', methods=['POST'])
def process_transaction():
    """Process a transaction by ambassador"""
    data = request.json
    
    if 'qr_data' not in data or 'ambassador_id' not in data:
        return jsonify({'success': False, 'message': 'Missing QR data or ambassador ID'}), 400
    
    try:
        # Parse QR code data
        qr_info = json.loads(data['qr_data'])
        transaction_id = qr_info['transaction_id']
        amount = float(qr_info['amount'])
        
        # Simulate processing
        network_status = sync_manager.get_network_status()
        
        if network_status['is_online']:
            # Process immediately
            message = f"Transaction {transaction_id} processed online"
            status = "completed"
        else:
            # Store offline
            message = f"Transaction {transaction_id} stored offline - will sync when network returns"
            status = "offline_pending"
        
        # Calculate commission (5%)
        commission = amount * 0.05
        
        return jsonify({
            'success': True,
            'transaction_id': transaction_id,
            'amount': amount,
            'commission': commission,
            'status': status,
            'network_online': network_status['is_online'],
            'message': message
        })
        
    except json.JSONDecodeError:
        return jsonify({'success': False, 'message': 'Invalid QR code format'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'Processing error: {str(e)}'}), 500

@app.route('/api/sync/execute', methods=['POST'])
def execute_sync():
    """Execute synchronization of offline transactions"""
    result = sync_manager.sync_transactions()
    return jsonify(result)

@app.route('/api/ambassador/stats/<ambassador_id>', methods=['GET'])
def get_ambassador_stats(ambassador_id):
    """Get statistics for specific ambassador"""
    stats = sync_manager.get_ambassador_stats(ambassador_id)
    
    if not stats:
        return jsonify({'success': False, 'message': 'Ambassador not found'}), 404
    
    return jsonify({'success': True, 'data': stats})

@app.route('/api/system/overview', methods=['GET'])
def get_system_overview():
    """Get overall system statistics"""
    overview = sync_manager.get_system_overview()
    return jsonify({'success': True, 'data': overview})

@app.route('/api/demo/reset', methods=['POST'])
def reset_demo():
    """Reset demo data for fresh presentation"""
    try:
        # Re-initialize database
        sync_manager.init_database()
        
        # Create some sample offline transactions
        tx1 = sync_manager.create_offline_transaction("DEMO001", "AMB001", 299, "Smartphone Cover")
        tx2 = sync_manager.create_offline_transaction("DEMO002", "AMB002", 599, "Bluetooth Headphones")
        tx3 = sync_manager.create_offline_transaction("DEMO003", "AMB001", 199, "Phone Charger")
        
        return jsonify({
            'success': True,
            'message': 'Demo reset successfully',
            'sample_transactions': [tx1, tx2, tx3]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Reset failed: {str(e)}'}), 500

@app.route('/dashboard')
def dashboard():
    """System dashboard with live statistics"""
    overview = sync_manager.get_system_overview()
    network_status = sync_manager.get_network_status()
    
    return render_template('dashboard.html', 
                         overview=overview, 
                         network_status=network_status)

@app.route('/ambassador/<ambassador_id>')
def ambassador_profile(ambassador_id):
    """Individual ambassador profile page"""
    stats = sync_manager.get_ambassador_stats(ambassador_id)
    
    if not stats:
        return "Ambassador not found", 404
    
    return render_template('ambassador_profile.html', 
                         ambassador=stats,
                         ambassador_id=ambassador_id)

# Demo automation routes

@app.route('/demo/auto-flow')
def auto_demo():
    """Automated demo flow for presentations"""
    return render_template('auto_demo.html')

@app.route('/api/demo/step/<int:step>', methods=['POST'])
def demo_step(step):
    """Execute specific demo steps"""
    try:
        if step == 1:
            # Step 1: Create offline transaction
            tx_id = sync_manager.create_offline_transaction("DEMO_CUSTOMER", "AMB001", 299, "Demo Product")
            return jsonify({
                'success': True,
                'message': 'Offline transaction created',
                'transaction_id': tx_id,
                'step': 'Transaction Created'
            })
            
        elif step == 2:
            # Step 2: Show offline status
            network_status = sync_manager.get_network_status()
            pending = sync_manager.get_pending_transactions()
            return jsonify({
                'success': True,
                'message': f'Network offline - {len(pending)} transactions pending',
                'network_online': network_status['is_online'],
                'pending_count': len(pending),
                'step': 'Offline Mode Demonstrated'
            })
            
        elif step == 3:
            # Step 3: Toggle network online
            new_status = sync_manager.simulate_network_toggle()
            return jsonify({
                'success': True,
                'message': 'Network brought online',
                'network_online': new_status,
                'step': 'Network Online'
            })
            
        elif step == 4:
            # Step 4: Execute sync
            result = sync_manager.sync_transactions()
            return jsonify({
                'success': True,
                'message': result['message'],
                'synced_count': result.get('synced_count', 0),
                'step': 'Synchronization Complete'
            })
            
        else:
            return jsonify({'success': False, 'message': 'Invalid demo step'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Demo step failed: {str(e)}'}), 500

@app.route('/logout')
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

if __name__ == '__main__':
    init_db()
    sync_manager.init_database()  # Ensure sync_manager DB init if needed
    app.run(debug=True, host='0.0.0.0', port=5000)
