# sync_manager.py - Add this file to your project for enhanced functionality

import sqlite3
import json
import time
from datetime import datetime, timedelta
import random

class SevaPaySyncManager:
    def __init__(self, db_path='transactions.db'):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT UNIQUE,
                customer_id TEXT,
                ambassador_id TEXT,
                amount REAL,
                product_name TEXT,
                status TEXT DEFAULT 'pending',
                created_offline INTEGER DEFAULT 1,
                sync_status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                synced_at TIMESTAMP NULL
            )
        ''')
        
        # Ambassadors table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ambassadors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ambassador_id TEXT UNIQUE,
                name TEXT,
                location TEXT,
                total_transactions INTEGER DEFAULT 0,
                total_earnings REAL DEFAULT 0.0,
                commission_rate REAL DEFAULT 0.05,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        # Network status table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS network_status (
                id INTEGER PRIMARY KEY,
                is_online INTEGER DEFAULT 0,
                last_sync TIMESTAMP,
                pending_sync_count INTEGER DEFAULT 0
            )
        ''')
        
        # Insert default network status
        cursor.execute('INSERT OR IGNORE INTO network_status (id, is_online) VALUES (1, 0)')
        
        conn.commit()
        conn.close()
        
        # Seed some demo data
        self.seed_demo_data()
    
    def seed_demo_data(self):
        """Add demo data for presentation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Sample ambassadors
        ambassadors = [
            ('AMB001', 'राज चाय वाला (Raj Tea Stall)', 'Banda, UP', 25, 750.0),
            ('AMB002', 'सुनीता जनरल स्टोर (Sunita General Store)', 'Chitrakoot, UP', 18, 540.0),
            ('AMB003', 'अमित मोबाइल रिपेयर (Amit Mobile Repair)', 'Hamirpur, UP', 32, 960.0)
        ]
        
        for amb in ambassadors:
            cursor.execute('''
                INSERT OR IGNORE INTO ambassadors 
                (ambassador_id, name, location, total_transactions, total_earnings) 
                VALUES (?, ?, ?, ?, ?)
            ''', amb)
        
        conn.commit()
        conn.close()
    
    def create_offline_transaction(self, customer_id, ambassador_id, amount, product_name):
        """Create a new offline transaction"""
        transaction_id = f"TXN{int(time.time())}{random.randint(100, 999)}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO transactions 
            (transaction_id, customer_id, ambassador_id, amount, product_name, status, created_offline)
            VALUES (?, ?, ?, ?, ?, 'offline_pending', 1)
        ''', (transaction_id, customer_id, ambassador_id, amount, product_name))
        
        conn.commit()
        conn.close()
        
        return transaction_id
    
    def get_pending_transactions(self):
        """Get all transactions pending synchronization"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM transactions 
            WHERE sync_status = 'pending' AND created_offline = 1
            ORDER BY created_at ASC
        ''')
        
        transactions = cursor.fetchall()
        conn.close()
        
        return transactions
    
    def simulate_network_toggle(self):
        """Toggle network status for demo purposes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT is_online FROM network_status WHERE id = 1')
        current_status = cursor.fetchone()[0]
        
        new_status = 1 - current_status  # Toggle between 0 and 1
        cursor.execute('UPDATE network_status SET is_online = ? WHERE id = 1', (new_status,))
        
        conn.commit()
        conn.close()
        
        return bool(new_status)
    
    def get_network_status(self):
        """Get current network status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT is_online, pending_sync_count FROM network_status WHERE id = 1')
        result = cursor.fetchone()
        conn.close()
        
        return {
            'is_online': bool(result[0]),
            'pending_count': result[1] if result[1] else 0
        }
    
    def sync_transactions(self):
        """Simulate synchronization of offline transactions"""
        if not self.get_network_status()['is_online']:
            return {'success': False, 'message': 'Network offline'}
        
        pending_transactions = self.get_pending_transactions()
        
        if not pending_transactions:
            return {'success': True, 'message': 'No transactions to sync', 'synced_count': 0}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        synced_count = 0
        current_time = datetime.now()
        
        for transaction in pending_transactions:
            transaction_id = transaction[1]  # transaction_id is at index 1
            ambassador_id = transaction[3]   # ambassador_id is at index 3
            amount = transaction[4]          # amount is at index 4
            
            # Simulate processing delay
            time.sleep(0.1)
            
            # Update transaction status
            cursor.execute('''
                UPDATE transactions 
                SET sync_status = 'synced', status = 'completed', synced_at = ?
                WHERE transaction_id = ?
            ''', (current_time, transaction_id))
            
            # Update ambassador earnings
            commission = amount * 0.05  # 5% commission
            cursor.execute('''
                UPDATE ambassadors 
                SET total_transactions = total_transactions + 1,
                    total_earnings = total_earnings + ?
                WHERE ambassador_id = ?
            ''', (commission, ambassador_id))
            
            synced_count += 1
        
        # Update network status
        cursor.execute('''
            UPDATE network_status 
            SET last_sync = ?, pending_sync_count = 0 
            WHERE id = 1
        ''', (current_time,))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True, 
            'message': f'Successfully synced {synced_count} transactions',
            'synced_count': synced_count
        }
    
    def get_ambassador_stats(self, ambassador_id):
        """Get statistics for a specific ambassador"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT name, location, total_transactions, total_earnings, status
            FROM ambassadors WHERE ambassador_id = ?
        ''', (ambassador_id,))
        
        ambassador = cursor.fetchone()
        
        if not ambassador:
            conn.close()
            return None
        
        # Get recent transactions
        cursor.execute('''
            SELECT transaction_id, amount, product_name, status, created_at
            FROM transactions 
            WHERE ambassador_id = ? 
            ORDER BY created_at DESC 
            LIMIT 10
        ''', (ambassador_id,))
        
        recent_transactions = cursor.fetchall()
        conn.close()
        
        return {
            'name': ambassador[0],
            'location': ambassador[1],
            'total_transactions': ambassador[2],
            'total_earnings': ambassador[3],
            'status': ambassador[4],
            'recent_transactions': recent_transactions
        }
    
    def get_system_overview(self):
        """Get overall system statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total transactions
        cursor.execute('SELECT COUNT(*) FROM transactions')
        total_transactions = cursor.fetchone()[0]
        
        # Pending sync count
        cursor.execute('SELECT COUNT(*) FROM transactions WHERE sync_status = "pending"')
        pending_sync = cursor.fetchone()[0]
        
        # Total earnings
        cursor.execute('SELECT SUM(total_earnings) FROM ambassadors')
        total_earnings = cursor.fetchone()[0] or 0
        
        # Active ambassadors
        cursor.execute('SELECT COUNT(*) FROM ambassadors WHERE status = "active"')
        active_ambassadors = cursor.fetchone()[0]
        
        # Network status
        network_status = self.get_network_status()
        
        conn.close()
        
        return {
            'total_transactions': total_transactions,
            'pending_sync': pending_sync,
            'total_earnings': round(total_earnings, 2),
            'active_ambassadors': active_ambassadors,
            'network_online': network_status['is_online'],
            'revenue_impact': round(total_transactions * 299, 2),  # Assuming avg ₹299 per transaction
            'market_penetration': min(100, (total_transactions / 1000) * 100)  # Demo calculation
        }

# Demo usage and testing functions
def demo_offline_flow():
    """Demonstrate the complete offline flow"""
    sync_manager = SevaPaySyncManager()
    
    print("🏪 Amazon Seva Pay - Offline Transaction Demo")
    print("=" * 50)
    
    # Create offline transactions
    print("\n1. Creating offline transactions...")
    tx1 = sync_manager.create_offline_transaction("CUST001", "AMB001", 299, "Smartphone Cover")
    tx2 = sync_manager.create_offline_transaction("CUST002", "AMB002", 599, "Bluetooth Headphones")
    tx3 = sync_manager.create_offline_transaction("CUST003", "AMB001", 199, "Phone Charger")
    
    print(f"✅ Created transactions: {tx1}, {tx2}, {tx3}")
    
    # Show network status
    network_status = sync_manager.get_network_status()
    print(f"\n2. Network Status: {'🟢 Online' if network_status['is_online'] else '🔴 Offline'}")
    
    # Show pending transactions
    pending = sync_manager.get_pending_transactions()
    print(f"📊 Pending sync: {len(pending)} transactions")
    
    # Toggle network online
    print("\n3. Bringing network online...")
    sync_manager.simulate_network_toggle()
    
    # Sync transactions
    print("4. Synchronizing transactions...")
    sync_result = sync_manager.sync_transactions()
    print(f"✅ {sync_result['message']}")
    
    # Show final stats
    print("\n5. Final System Overview:")
    stats = sync_manager.get_system_overview()
    for key, value in stats.items():
        print(f"   {key}: {value}")

if __name__ == "__main__":
    demo_offline_flow()
