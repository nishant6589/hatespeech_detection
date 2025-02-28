from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
# Create your views here.
def loginPage(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user_obj = User.objects.filter(username = username)
        if not user_obj.exists():
            messages.warning(request, "Account not found verified")
            return HttpResponseRedirect(request.path_info)
        
        user_obj = authenticate(username = username, password = password)

        if user_obj:
            login(request, user_obj)
            messages.warning(request, "Login successful")
            return  redirect('/')
        else:
            messages.warning(request, "Invalid Credentials")
            return render(request, 'account/login.html')
    return render(request, 'account/login.html')

def registerPage(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')

        user_obj = User.objects.filter(username = username)
        
        if user_obj.exists():
            messages.warning(request, "User already exists")
            return HttpResponseRedirect(request.path_info)

        user_obj = User.objects.create(first_name = first_name, last_name= last_name,  username = username)
        user_obj.set_password(password)
        user_obj.save()
        messages.warning(request, "User created successfully")
        return HttpResponseRedirect(request.path_info)
    
    return render(request, 'account/register.html')

def logoutPage(request):
    logout(request)
    messages.warning(request, "Logout successful")
    return HttpResponseRedirect('/')
