from django.shortcuts import render
from .serializers import UserSerializers,TokenSerializer
from rest_framework import generics,authentication,permissions
from rest_framework.settings import api_settings
from rest_framework.authtoken.views import ObtainAuthToken

class UserView(generics.CreateAPIView):
    serializer_class = UserSerializers

class CreateTokenView(ObtainAuthToken):
    serializer_class = TokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES

class ManageUserView(generics.RetrieveUpdateAPIView): #manage authenticated user
    serializer_class = UserSerializers
    authentication_classes =[authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user