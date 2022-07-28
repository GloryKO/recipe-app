from pyexpat import model
from attr import field
from rest_framework import serializers
from food_recipe_app.models import Ingredient, Recipe,Tag


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields =['id','name']
        read_only_fields=['id']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields =['id','name']
        read_only_fields =['id']

class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True,required=False)
    ingredients = IngredientSerializer(many=True,required=False)

    class Meta:
        model = Recipe
        fields =['id','title','time_minutes','price','link','tags','ingredients',]
        read_only_fields =['id']

    def get_or_create_tags(self,tags,recipe):
        auth_user = self.context['request'].user
        for tag in tags:
            tag_obj,created =Tag.objects.get_or_create(user=auth_user,**tag,)
            recipe.tags.add(tag_obj)

    def get_or_create_ingredients(self,ingredients,recipe):
        auth_user = self.context['request'].user
        for ingredient in ingredients:
            ingredient_obj,create = Ingredient.objects.get_or_create(user=auth_user,**ingredient,)
            recipe.ingredients.add(ingredient_obj)

    
    def create(self,validated_data):
        tags = validated_data.pop('tags',[])
        ingredients = validated_data.pop('ingredients',[])
        recipe = Recipe.objects.create(**validated_data)
        self.get_or_create_tags(tags,recipe)
        self.get_or_create_ingredients(ingredients,recipe)
        
        return recipe

    def update(self,instance,validated_data):
        tags =validated_data.pop('tags',None)
        ingredients = validated_data.pop('ingredients',None)

        if tags is not None:
            instance.tags.clear()
            self.get_or_create_tags(tags,instance)
        if ingredients is not None:
            self.get_or_create_ingredients(ingredients,instance)

            for attr,value in validated_data.items():
                setattr(instance,attr,value)
            instance.save()
            return instance
            




class RecipeDetailSerializer(serializers.ModelSerializer):
    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields +['description','image']


class RecipeImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ['id','image']
        read_only_fields =  ['id']
        extra_kwargs = {'image':{'required':'True'}}
