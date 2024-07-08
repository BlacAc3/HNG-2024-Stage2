import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'authOrganisation.settings')
import django
django.setup()



import unittest
import requests
import jwt
import json
from rest_framework_simplejwt.tokens import AccessToken
from datetime import datetime, timedelta, timezone
from rest_framework import status
from django.test import TestCase
from rest_framework.test import APIClient
from api.models import CustomUser, Organisation
from django.conf import settings


class TokenGenerationTestCase(TestCase):
    
    def setUp(self):
        self.user = CustomUser.objects.create(
            firstName="John",
            lastName="Doe",
            email="john.doe@example.com",
            password="testpassword"
        )
        self.user.save()
        
    def test_token_expiry(self):
        access_token = AccessToken.for_user(self.user)
        
        # Check token expiry time (default is 1 hour)
        expiry_time = access_token['exp']
        now = datetime.now(timezone.utc).timestamp()
        
        self.assertGreaterEqual(expiry_time, now)
        self.assertLessEqual(expiry_time, now + 3600)  # 3600 seconds = 1 hour
        print(f"---Token Expiration - 👌✅")
    
    def test_token_contains_user_details(self):
        access_token = AccessToken.for_user(self.user)
        str_access_token = str(access_token)
        
        decoded_token = jwt.decode(str_access_token, settings.SECRET_KEY, algorithms=["HS256"])  # Decode the token
        # Verify user details in the token
        self.assertEqual(decoded_token['userId'], str(self.user.userId))
        self.user.delete()
        print(f"---Token Encoding with User details - 👌✅")


class AccessControlTestCase(TestCase):
    
    def setUp(self):
        self.client = APIClient()
        self.base_url = 'http://localhost:8000/'
        self.access_token = ""
        self.user1_password = "testpassword"
        self.user2_password = "testpassword"

        # Create users via API
        self.user1_instance = self.create_user("John", "Doe", "john11.doe@example.com", "testpassword")
        self.user2_instance = self.create_user("Jane", "Smith", "jane11.smith@example.com", "testpassword")
        
        # Create organisations via API
        self.org1 = self.create_organisation(self.user1_instance, "John's Organisation", "John's test organization", "john11.doe@example.com", "testpassword")
        self.org2 = self.create_organisation(self.user2_instance, "Jane's Organisation", "Jane's test organization", "jane11.smith@example.com", "testpassword")
    
    def create_user(self, first_name, last_name, email, password):
        url = f'{self.base_url}auth/register'
        self.password = password
        data = {
            "firstName": first_name,
            "lastName": last_name,
            "email": email,
            "password": password
        }
        response = self.client.post(url, data, format='json')
        result = response.json()
        self.access_token = result["data"]["accessToken"]
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        id = response.json()["data"]["user"]["userId"]
        instance = CustomUser.objects.get(userId=id)
        return instance
    
    def create_organisation(self, owner, name, description, email, password):
        url = f'{self.base_url}api/organisations'
        data = {
            "name": name,
            "description": description
        }
        # login
        self.login(email, password)
        # setup access token credentials  
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        print(f"---Enabled Organisation Creation - 🏢🌱")

        id = response.json()["data"]["orgId"]
        instance = Organisation.objects.get(orgId=id)
        return instance

    def login(self, email, password):
        url = f"{self.base_url}auth/login"
        data = {"email": email, "password": password}
        response = self.client.post(url, data, format="json")
        self.access_token = response.json()["data"]["accessToken"]
        return response.json()
    
    def test_access_to_organisation(self):
        # Add user1 to org1
        self.add_user(self.user1_instance.userId, self.org1.orgId)
        print(self.org1.members)
        # Add user2 to org2
        self.add_user(self.user2_instance.userId, self.org2.orgId)

        # User 1 should have access to org1
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

        self.login(self.user1_instance.email, self.user1_password)
        response = self.client.get(f'{self.base_url}api/organisations/{self.org1.orgId}')
        self.assertEqual(response.status_code, 404)
        print(f"---User1 has access to Organisation1- 👤1️⃣🔑🏢1️⃣")
        
        # User 1 should have access to org2
        response = self.client.get(f'{self.base_url}api/organisations/{self.org2.orgId}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(f"---User1 has no access to Organisation2- 👤1️⃣🔑🏢2️⃣")
        
        # User 2 should have access to org2
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        self.login(self.user2_instance.email, self.user2_password)
        response = self.client.get(f'{self.base_url}api/organisations/{self.org2.orgId}')
        self.assertEqual(response.status_code, 404)
        print(f"---User2 has no access to Organisation1- 👤2️⃣🔑🏢1️⃣")
        
        # User 2 should have access to org1
        response = self.client.get(f'{self.base_url}api/organisations/{self.org1.orgId}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(f"---User2 has access to Organisation2- 👤2️⃣🔑🏢2️⃣")

    def add_user(self, userId, orgId):
        url = f"http://localhost:8000/api/organisations/{orgId}/users"
        data = {
            "userId": userId
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        print(f"---Added user to organisation - {response.json()}")


class CombinedTestCase(TestCase):

    def setUp(self):
        self.base_url = 'http://localhost:8000/auth/register'
        self.headers = {'Content-Type': 'application/json'}
        self.client = APIClient()
        
        self.create_user_response = self.create_user(
            first_name="John",
            last_name="Doe",
            email="johnnew.doe@example.com",
            password="testpassword"
        )

        self.dup_data1 = {
            "firstName": "John",
            "lastName": "Doe",
            "email": "john2doe@example.com",
            "password": "testpassword"
        }
        self.response_data1 = self.client.post(self.base_url, self.dup_data1, format="json")

        self.dup_data2 = {
            "firstName": "Jane",
            "lastName": "Smith",
            "email": "john2doe@example.com",  # Same email as data1
            "password": "testpassword"
        }
        self.response_data2 = self.client.post(self.base_url, self.dup_data2, format="json")

    def create_user(self, first_name, last_name, email, password):
        data = {
            "firstName": first_name,
            "lastName": last_name,
            "email": email,
            "password": password
        }
        return self.client.post(self.base_url, data, format="json")

    def test_register_user_success(self):
        response = self.create_user_response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        print(f"---User Registered- 🎉👤✔️")
        self.assertIn('accessToken', response.json()["data"])
        print(f"---Found Access token in JSON- 🔍🔑🔍")
        self.assertIn('user', response.json()["data"])
        print(f"---Found User Details in JSON- 🔍👤🔍")

        # Extract access token for subsequent requests
        access_token = response.json()["data"]['accessToken']
        # Example usage: make authenticated request
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get('http://localhost:8000/api/organisations')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(f"---Allowing only authenticated access - 🔒🔑✔️")

    def test_missing_required_fields(self):
        data = {
            "firstName": "John",
            "lastName": "Doe",
        }
        response = self.client.post(self.base_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        print(f"---Successfully Rejected Bad Request Body - ❌📬🚫")
        self.assertIn('errors', response.json())
        print(f"---Errors handled - 🛡️🐛✔️")

    def test_duplicate_email(self):
        # Register first user
        self.assertEqual(self.response_data1.status_code, status.HTTP_201_CREATED)
        print(f"---Attempting Duplication - 🔄📑🤔")

        # Attempt to register second user with same email
        self.assertEqual(self.response_data2.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        print(f"---Duplication prevented - 🚫📑💡")
        self.assertIn('errors', self.response_data2.json())
        print(f"---Errors handled- 🛡️🐛✔️")

if __name__ == '__main__':
    unittest.main()

