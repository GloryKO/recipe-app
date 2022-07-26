from ast import arg
from http import client
from unicodedata import name
from rest_framework.test import APIClient
from django.test import TestCase
from django.urls import reverse
from rest_framework import  status
from food_recipe_app.models import Recipe, Tag
from django.contrib.auth import get_user_model
from recipe.serializers import TagSerializer
from recipe.tests.test_recipe_api import create_recipe

def detail_url(tag_id):
    return reverse('recipe:tag-detail',args=[tag_id])


TAGS_URL = reverse('recipe:tag-list')

def create_user(email='test@example.com',password= 'testpass'):
    return get_user_model().objects.create_user(email=email,password=password)

class TestPublicApiTags(TestCase):
    def setUp(self):
        self.client = APIClient()
    
    def test_auth_required(self):
        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code,status.HTTP_401_UNAUTHORIZED)

class TestPrivateApiTags(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)
    
    def test_retrieve_tags(self):
        tag1 = Tag.objects.create(user=self.user,name='Vegan')
        tag2 = Tag.objects.create(user=self.user,name='Vegie')

        res = self.client.get(TAGS_URL)
        tags= Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags,many=True)
        self.assertEqual(res.status_code,status.HTTP_200_OK)
        self.assertEqual(res.data,serializer.data)
    
    def test_tags_related_to_user(self):
        user2= create_user(email='user2@example.com')
        Tag.objects.create(user=user2,name='Fruity')
        tag = Tag.objects.create(user=self.user,name='Muffin')
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code,status.HTTP_200_OK)
        self.assertEqual(len(res.data),1)
        self.assertEqual(res.data[0]['name'],tag.name)

    def test_tag_update(self):
        tag =Tag.objects.create(user=self.user,name='After Diner')
        payload ={'name':'Desert'}
        url = detail_url(tag.id)
        res =self.client.patch(url,payload)
        self.assertEqual(res.status_code,status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name,payload['name'])

    def test_delete_tag(self):
        tag= Tag.objects.create(user=self.user,name='BreakFast')
        url = detail_url(tag.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code,status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.filter(user=self.user).exists())
    
    

