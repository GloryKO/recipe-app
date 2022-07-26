from ast import arg
from genericpath import exists
from os import link
from turtle import title
from django.contrib.auth import get_user_model
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from yaml import serialize

from food_recipe_app.models import Ingredient, Recipe,Tag
from recipe.serializers import RecipeSerializer,RecipeDetailSerializer

RECIPE_URL = reverse('recipe:recipe-list')

def detail_url(recipe_id):
    return reverse('recipe:recipe-detail',args=[recipe_id])

def create_recipe(user,**params):
    defaults = {
        'title':'Sample Recipe title',
        'time_minutes':22,
        'price': Decimal('5.59'),
        'description':'Sample Recipe description',
        'link':'https://example.com/recipe.pdf',

    }
    defaults.update(params)
    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


class PublicAPiTests(TestCase): #test recipe for unauthenticated users

    def setUp(self):
        self.client = APIClient()
    
    def test_auth_required(self):
        res = self.client.get(RECIPE_URL)
        self.assertEqual(res.status_code,status.HTTP_401_UNAUTHORIZED)

class PrivateApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user('user@example.com',
            'testpass123',)
        self.client.force_authenticate(self.user)
    
    def test_retrive_recipes(self):
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)
        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code,status.HTTP_200_OK)
        self.assertEqual(res.data,serializer.data)
    
    def test_recipe_limited_to_user(self):
        other_user = get_user_model().objects.create_user(
            'other@example.com','otherpass123'
        )
        create_recipe(other_user)
        create_recipe(self.user)

        res =self.client.get(RECIPE_URL)
        recipe = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipe,many=True)
        self.assertEqual(res.status_code,status.HTTP_200_OK)
        self.assertEqual(res.data,serializer.data)
    
    def test_get_recipe_detail(self):
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res= self.client.get(url)
        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data,serializer.data)
        self.assertEqual(res.status_code,status.HTTP_200_OK)
    

    def test_create_recipe(self):
        payload ={
            'title':'Sample recipe',
            'time_minutes': 30,
            'price':Decimal('5.99'),
         }
        res = self.client.post(RECIPE_URL,payload)
        self.assertEqual(res.status_code,status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for k,v in payload.items():
            self.assertEqual(getattr(recipe,k),v)
        self.assertEqual(recipe.user,self.user)
    
    def test_partial_update(self):
        link_ ='https://example.com/recipe.pdf'
        recipe = create_recipe(
            user=self.user,
            title ='sample title ',
            link=link_,
          )
        payload = {'title':'New recipe title'}
        url = detail_url(recipe.id)
        res = self.client.patch(url,payload)
        self.assertEqual(res.status_code,status.HTTP_200_OK)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title,payload['title'])
        self.assertEqual(recipe.user,self.user)
        self.assertEqual(recipe.link,link_)
    
    def test_full_update(self):
        link_ ='https://example.com/recipe.pdf'
        recipe = create_recipe(
            user=self.user,
            title ='sample title ',
            link=link_,
            description ='Sample description',
          )
        payload = {'title':'New recipe title','description':'New recipe description',
        'link':'https://example.com/new-recipe.pdf','price':Decimal('2.50'),
        'time_minutes':10,
        }
        url = detail_url(recipe.id)
        res = self.client.put(url,payload)
        self.assertEqual(res.status_code,status.HTTP_200_OK)
        recipe.refresh_from_db()
        for k,v in payload.items():
            self.assertEqual(getattr(recipe,k),v)
        self.assertEqual(self.user,recipe.user )
    
    def test_delete_recipe(self):
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res =self.client.delete(url)
        self.assertEqual(res.status_code,status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())
    
    def test_delete_other_user_recipe_gives_error(self):
        new_user = get_user_model().objects.create_user(email='newuse@example.com',password='pass123')
        recipe = create_recipe(new_user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code,status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())


    def test_create_recipe_with_new_tags(self):
        payload = {
            'title':'Thai Cury',
            'time_minutes':20,
            'price':Decimal('3.00'),
            'tags':[{'name':'Thai'},{'name':'Dinner'}],
        }
        res =self.client.post(RECIPE_URL,payload,format='json')
        self.assertEqual(res.status_code,status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(),1)
        recipe =recipes[0]
        self.assertEqual(recipe.tags.count(),2)
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name =tag['name'],
                user =self.user,

            ).exists()
            self.assertTrue(exists)
    
    def test_create_recipe_with_existing_tags(self):
        tag_indian = Tag.objects.create(user=self.user,name='Indian')
        payload = {
            'title':'Pongal',
            'time_minutes':60,
            'price':Decimal('3.00'),
            'tags':[{'name':'Indian'},{'name':'Breakfast'}],
        }
        res =self.client.post(RECIPE_URL,payload,format='json')
        self.assertEqual(res.status_code,status.HTTP_201_CREATED)
        recipes =Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(),1)
        recipe= recipes[0]
        self.assertEqual(recipe.tags.count(),2)
        self.assertIn(tag_indian,recipe.tags.all())
        for tag in  payload['tags']:
            exists = recipe.tags.filter(
                user = self.user,
                name=tag['name']
            ).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        recipe = create_recipe(user=self.user)
        payload = {
            'tags':[{'name':'Lunch'},]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url,payload,format='json')
        
        self.assertEqual(res.status_code,status.HTTP_200_OK)
        new_tag =Tag.objects.get(user=self.user,name='Lunch')
        self.assertIn(new_tag,recipe.tags.all())

    
    def test_update_recipe_assign_tag(self):
        tag_breakfast = Tag.objects.create(user=self.user,name='Breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user,name='Lunch')
        payload ={'tags':[{'name':'Lunch'}],}
        url = detail_url(recipe.id)
        res =self.client.patch(url,payload,format='json')
        self.assertEqual(res.status_code,status.HTTP_200_OK)
        self.assertIn(tag_lunch,recipe.tags.all())
        self.assertNotIn(tag_breakfast,recipe.tags.all())
    
    
    def test_clear_recipe_tags(self):
        tag =Tag.objects.create(user=self.user,name='Dessert')
        recipe =create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload ={'tags':[]}
        url = detail_url(recipe.id)
        res = self.client.patch(url,payload,format='json')
        
        self.assertEqual(res.status_code,status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(),0)

    def test_create_recipe_with_new_ingredients(self):
        payload ={
            'title':'Cauliflower Tacos',
            'time_minutes':60,
            'price':Decimal('4.30'),
            'ingredients':[{'name':'Cauliflower'},{'name':'Salt'}],
        }
        res = self.client.post(RECIPE_URL,payload,format='json')
        self.assertEqual(res.status_code,status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(),1)
        recipe =recipes[0]
        self.assertEqual(recipe.ingredients.count(),2)
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(name=ingredient['name'],user=self.user).exists()
            self.assertTrue(exists)
    
    def test_create_recipe_with_existing_ingredient(self):
        ingredient =Ingredient.objects.create(user=self.user,name='Lemon')
        payload ={
            'title':'Vietnamese Soup',
            'time_minutes':20,
            'price':'2.55',
            'ingredients':[{'name':'Lemon'},{'name':'Fish Sauce'}],
        }
        res = self.client.post(RECIPE_URL,payload,format='json')
        self.assertEqual(res.status_code,status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(),1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(),2)
        self.assertIn(ingredient,recipe.ingredients.all())
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name = ingredient['name'],
                user = self.user
            ).exists()
            self.assertTrue(exists)