from django.shortcuts import render
from django.http import HttpResponse

def home(render):
    return HttpResponse('fala meu querido!')