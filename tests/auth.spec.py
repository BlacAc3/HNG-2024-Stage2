import unittest
import requests

class RegisterEndpointTestCase(unittest.TestCase):
    
    def setUp(self):
        self.base_url = 'http://localhost:8000/api/auth/register/'
        self.headers = {'Content-Type': 'application/json'}
    
    def test_register_user_success(self):
        data = {
            "firstName": "John",
            "lastName": "Doe",
            "email": "john.doe@example.com",
            "password": "testpassword"
        }
        response = requests.post(self.base_url, json=data, headers=self.headers)
        
        self.assertEqual(response.status_code, 201)
        self.assertIn('accessToken', response.json())
        self.assertIn('user', response.json())
        # Add more assertions for user details
        
    def test_missing_required_fields(self):
        data = {
            "firstName": "John",
            "lastName": "Doe"
            # Missing 'email' and 'password'
        }
        response = requests.post(self.base_url, json=data, headers=self.headers)
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('errors', response.json())
        # Add more assertions for specific error messages
    
    def test_duplicate_email(self):
        data1 = {
            "firstName": "John",
            "lastName": "Doe",
            "email": "john.doe@example.com",
            "password": "testpassword"
        }
        data2 = {
            "firstName": "Jane",
            "lastName": "Smith",
            "email": "john.doe@example.com",  # Same email as data1
            "password": "testpassword"
        }
        
        # Register first user
        response1 = requests.post(self.base_url, json=data1, headers=self.headers)
        self.assertEqual(response1.status_code, 201)
        
        # Attempt to register second user with same email
        response2 = requests.post(self.base_url, json=data2, headers=self.headers)
        self.assertEqual(response2.status_code, 422)
        self.assertIn('errors', response2.json())
        # Add more assertions for specific error messages

if __name__ == '__main__':
    unittest.main()
