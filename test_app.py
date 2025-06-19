import unittest
import json
from app import app

class SevaPayTestCase(unittest.TestCase):
    
    def setUp(self):
        """Set up test client"""
        self.app = app.test_client()
        self.app.testing = True
    
    def test_index_page(self):
        """Test main page loads"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_generate_qr(self):
        """Test QR code generation"""
        test_data = {
            'customer_id': 'CUST001',
            'amount': 299.00,
            'product': 'Test Product'
        }
        response = self.app.post('/generate_qr', 
                               data=json.dumps(test_data),
                               content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('qr_code', data)
    
    def test_process_payment(self):
        """Test payment processing"""
        test_data = {
            'qr_code': 'QR001',
            'ambassador_id': 'AMB001',
            'amount': 299.00
        }
        response = self.app.post('/process_payment',
                               data=json.dumps(test_data),
                               content_type='application/json')
        self.assertEqual(response.status_code, 200)
    
    def test_sync_transactions(self):
        """Test transaction synchronization"""
        response = self.app.post('/sync_transactions')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('synced_count', data)
    
    def test_ambassador_dashboard(self):
        """Test ambassador dashboard access"""
        response = self.app.get('/ambassador/AMB001')
        self.assertEqual(response.status_code, 200)
    
    def test_customer_dashboard(self):
        """Test customer dashboard access"""
        response = self.app.get('/customer/CUST001')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
