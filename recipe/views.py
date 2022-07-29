from webbrowser import get
from django.shortcuts import render
from rest_framework import viewsets,mixins,status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from .serializers import IngredientSerializer, RecipeDetailSerializer, RecipeSerializer,TagSerializer,RecipeImageSerializer
from food_recipe_app.models import Ingredient, Recipe,Tag
from drf_spectacular.utils import extend_schema_view,extend_schema,OpenApiParameter,OpenApiTypes


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'tags',
                OpenApiTypes.STR,
                description='Comma seperated list of tags Ids to filter',

            ),
             OpenApiParameter(
                'ingredients',
                OpenApiTypes.STR,
                description='Comma seperated list of ingredients Ids to filter',

            ),
        ]
    )
)
class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]


    def params_to_ints(self,qs):
        return [int(str_id) for str_id in qs.split(',')] #convert a list of strings to integers

    def get_queryset(self):
        tags = self.request.query_params.get('tags')
        ingredients = self.request.query_params.get('ingredients')
        queryset = self.queryset
        if tags:
            tags_ids = self.params_to_ints(tags)
            queryset = queryset.filter(tags__id__in=tags_ids)
        if ingredients:
            ingredients_ids =self.params_to_ints(ingredients)
            queryset = queryset.flter(ingredients__id__in=ingredients_ids)

        return queryset.filter(
            user = self.user,
        ).order_by('-id').distinct()

        return self.queryset.filter(user=self.request.user).order_by('-id')
    
    def get_serializer_class(self):
        if self.action=='list':
            return RecipeSerializer
        elif self.action =='upload_image':
            return RecipeImageSerializer

    def perform_create(self,serializer):
        serializer.save(user=self.request.user)

    @action(methods=['POST'],detail=True,url_path='image-upload')
    # custom action to upload image to the recipe.detials =True means the action applies to the detial view of the modelviewset
    def upload_image(self,request,pk=None):
        recipe =self.get_object()
        serializer = self.get_serializer(recipe,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'assigned_only',
                OpenApiTypes.INT, enum=[0,1],
                description='Filter by items attached to a recipe .'
            )
        ]
    )
)
class BaseRecipeAttrViewSet(mixins.ListModelMixin,mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,viewsets.GenericViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        assigned_only = bool(int(self.request.query_params.get('assigned_only',0))
        
        )
        queryset = self.queryset
        if assigned_only:
            queryset = queryset.filter(recipe__isnull=False)
        return self.queryset.filter(user=self.request.user).order_by('-name')

class TagViewSet(BaseRecipeAttrViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    

class IngredientViewSet(BaseRecipeAttrViewSet):
    serializer_class =IngredientSerializer
    queryset = Ingredient.objects.all()
    