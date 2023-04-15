# Create your views here.
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from django.contrib.auth import get_user_model, authenticate
from django.shortcuts import get_object_or_404, redirect
from rest_framework.response import Response
from .serializers import RegisterSerializer
from rest_framework.views import APIView
from rest_framework import status
from dotenv import load_dotenv
import jwt
import os


class RegisterAPIView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token = TokenObtainPairSerializer.get_token(user)
            ###
            print(token)
            ###
            refresh_token = str(token)
            access_token = str(token.access_token)
            res = Response(
                {
                    "user": serializer.data,
                    "message": "회원가입 성공",
                    "token": {
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                    },
                },
                status=status.HTTP_201_CREATED,
            )
            res.set_cookie("access_token", access_token, httponly=True)
            res.set_cookie("refresh_token", refresh_token, httponly=True)
            return res
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AuthView(APIView):
    # 유저 정보 확인
    # 로그인 전 유저 정보를 jwt에서 추출
    def get(self, request):
        # 디코딩을 위한 시크릿키가 있는 env 활성화
        if "access_token" not in request.COOKIES:
            return redirect("accounts:register")
        load_dotenv()
        try:
            access_token = request.COOKIES.get("access_token")
            payload = jwt.decode(
                access_token, os.getenv("JWT_SECRET_KEY"), algorithms=["HS256"]
            )
            ###
            print(payload, 111111111111111)
            ###
            user_pk = payload.get("user_id")
            ###
            print(user_pk, 222222222222222)
            ###
            user = get_object_or_404(get_user_model(), pk=user_pk)
            serializer = RegisterSerializer(instance=user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except jwt.exceptions.ExpiredSignatureError:
            data = {
                "refresh_token": request.COOKIES.get("refresh_token", None),
            }
            serializer = TokenRefreshSerializer(data=data)
            if serializer.is_valid(raise_exception=True):
                access_token = serializer.data.get("access_token", None)
                refresh_token = serializer.data.get("refresh_token", None)
                payload = jwt.decode(
                    access_token, os.getenv("JWT_SECRET_KEY"), algorithms=["HS256"]
                )
                user_pk = payload.get("user_id")
                user = get_object_or_404(get_user_model(), pk=user_pk)
                serializer = RegisterSerializer(instance=user)
                res = Response(serializer.data, status=status.HTTP_200_OK)
                res.set_cookie("access_token", access_token)
                res.set_cookie("refresh_token", refresh_token)
                return res
            raise jwt.exceptions.InvalidTokenError
        except jwt.exceptions.InvalidTokenError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    # 로그인
    def post(self, request):
        user = authenticate(
            email=request.data.get("email"), password=request.data.get("password")
        )
        if user is not None:
            serializer = RegisterSerializer(user)
            token = TokenObtainPairSerializer.get_token(user)
            refresh_token = str(token)
            access_token = str(token.access_token)
            res = Response(
                {
                    "user": serializer.data,
                    "message": "로그인 성공",
                    "token": {
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                    },
                },
                status=status.HTTP_200_OK,
            )
            res.set_cookie("access_token", access_token, httponly=True)
            res.set_cookie("refresh_token", refresh_token, httponly=True)
            return res
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    # 로그아웃
    def delete(self, request):
        res = Response(
            {
                "message": "로그아웃 성공",
            },
            status=status.HTTP_202_ACCEPTED,
        )
        res.set_cookie("access_token", "")
        res.set_cookie("refresh_token", "")
        return res
