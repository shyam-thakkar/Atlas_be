from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()

class AuthTests(APITestCase):
    def test_signup(self):
        url = reverse('signup')
        data = {
            'email': 'test@example.com',
            'password': 'StrongPassword123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().email, 'test@example.com')

    def test_signup_invalid_email(self):
        url = reverse('signup')
        data = {
            'email': 'not-an-email',
            'password': 'password'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login(self):
        User.objects.create_user(email='test@example.com', password='StrongPassword123')
        url = reverse('login')
        data = {
            'email': 'test@example.com',
            'password': 'StrongPassword123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_invalid(self):
        User.objects.create_user(email='test@example.com', password='StrongPassword123')
        url = reverse('login')
        data = {
            'email': 'test@example.com',
            'password': 'WrongPassword'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
