from decimal import Decimal
from venv import create
from django.test import TestCase
from django.contrib.auth import get_user_model
from food_recipe_app import models


def create_user(email='testuser@example.com',password ='pass123'):
    return get_user_model().objects.create_user(email,password)

class ModelTests(TestCase):
    
    def test_user_created_with_email_success(self):
        email ="user1@example.com"
        password = "password1"
        user = get_user_model().objects.create_user( email=email,password=password)
        self.assertEqual(user.email,email)
        self.assertTrue(user.check_password(password))
    
    def test_normalized_email_success(self):
        sample_emails = [
            ['user1@EXAmple.com','user1@example.com'],
            ['user1@EXAMPLE.com','user1@example.com'],
            ['USER1@EXAmple.com','user1@example.com'],
            ]

        for email,expected in sample_emails:
            user = get_user_model().objects.create_user(email='user@example.com')
            self.assertEqual(user.email,expected) 
    
    def test_user_with_no_email_raises_error(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('','test123')

    def test_create_super_user(self):
        user = get_user_model().objects.create_superuser('test@example.com','test123')
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
    
    def test_create_recipe(self):
        user = get_user_model().objects.create_user(
            'test@example.com','testpass123'
        )
        recipe = models.Recipe.objects.create(
            user = user,
            title ='sample recipe',
            time_minutes =5,
            price = Decimal('5.50'),
            description ='sample description',
        )

        self.assertEqual(str(recipe),recipe.title)
    
    def test_create_tag(self):
        user = create_user()
        tag = models.Tag.objects.create(user=user,name ='Tag1')
        self.assertEqual(str(tag),tag.name)
    
    def test_create_ingredient(self):
        user = create_user()
        ingredient = models.Ingredient.objects.create(
            user=user
        )
        self.assertEqual(str(ingredient),ingredient.name)