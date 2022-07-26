from venv import create
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')

def create_user(**params): #create user with parameters passed in

    return get_user_model().objects.create_user(**params)

class PublicUserApiTests(TestCase):#incudes test for public users(unauthenticated)

    def setUp(self):
        self.client = APIClient()
    
    def test_create_user_success(self):
        payload ={
            'email':'test@example.com',
            'password':'testpass123',
            'name':'Test Name',
        }

        res = self.client.post(CREATE_USER_URL,payload)
        self.assertEqual(res.status_code,status.HTTP_201_CREATED)

        user = get_user_model().objects.get(email=payload['email'])
        self.assertTrue(user.check_password(payload['password']))

        self.assertNotIn('password',res.data) #check to make sure the password is not returned with the data
    
    def test_user_with_email_exists_error(self): #test if we return an error if user does not provide email
        payload ={
            'email':'test@example.com',
            'password':'testpass123',
            'name':'Test Name',
        }
        create_user(**payload)
        res =self.client.post(CREATE_USER_URL,payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    
    def test_password_too_short_error(self):
         payload ={
            'email':'test@example.com',
            'password':'test',
            'name':'Test Name',
         }

         res = self.client.post(CREATE_USER_URL,payload)
         self.assertEqual(res.status_code,status.HTTP_400_BAD_REQUEST)
         user_exists = get_user_model().objects.filter(email=payload['email']).exists()
         self.assertFalse(user_exists)
        
    
    def test_create_token_for_user(self):
        user_details ={
            'name':'testname',
            'email':'test@example.com',
            'password':'testpass123',
        }

        create_user(**user_details)
        payload ={
            'email':user_details['email'],
            'password':user_details['password']
        }
        res = self.client.post(TOKEN_URL,payload)
        self.assertEqual(res.status_code,status.HTTP_200_OK)

    def test_create_token_bad_credentials(self):
        create_user(email ='test@example',password ='goodpass')
        payload = {'email':'test@example.com','password':'badpass'}
        res = self.client.post(TOKEN_URL,payload)
        self.assertNotIn('token',res.data)
        self.assertEqual(res.status_code,status.HTTP_400_BAD_REQUEST)
    
    
    def test_create_token_with_blank_password(self):
        payload ={'emai':'test@example.com','password':''}
        res = self.client.post(TOKEN_URL,payload)
        self.assertNotIn('token',res.data)
        self.assertEqual(res.status_code,status.HTTP_400_BAD_REQUEST) 
    
    def test_retrieve_user_unauthenticated(self):
        res =self.client.get(ME_URL)
        self.assertEqual(res.status_code,status.HTTP_401_UNAUTHORIZED)
    

class PrivateUserAPiTests(TestCase):
    def setUp(self):
        self.user = create_user(
            email='test@example.com',
            password='testpass123',
            name='Test Name',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def retrieve_profile_success(self):
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code,status.HTTP_200_OK)
        self.assertEqual(res.data,{
            'name':self.user.name,
            'email':self.user.email,
        })
    
    def test_post_not_allowed(self):
        res = self.client.post(ME_URL,{})
        self.assertEqual(res.status_code,status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        payload = {'name':'updated name','password':'newpassword123'}
        res = self.client.patch(ME_URL,payload)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name,payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res.status_code,status.HTTP_200_OK)


