from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.template.context import RequestContext
from django.contrib.auth import login, logout
from django.core import serializers
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from .models import *
import json
from django.contrib import auth
from django.core.context_processors import csrf
from social_auth.backends import get_backend
from django.template import RequestContext
from django.core.mail import send_mail
import hashlib, datetime, random
from django.utils import timezone
from django.contrib.auth.models import User
from django import forms
from django.http import JsonResponse
from django.forms import ModelForm
from photobucket.models import *
from friends.models import Friendship
import datetime
from datetime import datetime
import feedparser
from django.conf import settings
from itertools import chain
# Create your views here.
current_month = datetime.now().month+6
print(current_month)


class UserCreationForm(forms.ModelForm):
	password1  = forms.CharField(label='Password', widget=forms.PasswordInput)
	password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput, help_text = "Should be same as Password")

	def __init__(self, *args, **kwargs):
		super(UserCreationForm, self).__init__(*args, **kwargs)
		self.fields['username'].help_text = ''
		for field in self.fields:
			self.fields[field].required = True

	class Meta:
		model = MyUser
		fields = ['username', 'email', 'first_name', 'last_name', 'gender', 'dob', 'phone']
	def clean_passwd2(self):
		passwd1 = self.cleaned_data.get("passwd1")
		passwd2 = self.cleaned_data.get("passwd2")
		if passwd1 and passwd2 and passwd1 != passwd2:
			raise forms.ValidationError("Passwords don't match")
		return passwd2
	def save(self, commit=True):
		user = super(UserCreationForm, self).save(commit = False)
		user.set_password(self.cleaned_data["password1"])
		user.email = self.cleaned_data['email']
		if commit:
			user.is_active = False
			user.save()
		return user
	#clean email field
	def clean_email(self):
		email = self.cleaned_data["email"]
		try:
			MyUser._default_manager.get(email=email)
		except MyUser.DoesNotExist:
			return email
		raise forms.ValidationError('duplicate email')

class profileForm(forms.ModelForm):
	class Meta:
		model = MyUser
		fields =  ['username', 'email', 'first_name', 'last_name', 'gender', 'dob', 'phone','profile_pic']
		
		
class profile_picForm(forms.ModelForm):
	class Meta:
		model = MyUser
		fields =  ['profile_pic']
		
class userinfo_Form(forms.ModelForm):
    class Meta:
        model = UserInfo
       # def selected_cuisine_labels(self):
        #    return [label for value, label in self.fields['liked_cuisine'].choices if value in self['liked_cuisine'].value()]
        exclude = ['user']
    #liked_cuisine = forms.MultipleChoiceField(choices=CUISINES_CHOICES, widget=forms.CheckboxSelectMultiple())
		
def mylogin(request):
    context = RequestContext(request,
                           {'request': request,
                            'user': request.user})
    if   request.user.is_authenticated():
        return render(request,'landing.html')#{'PUSHER_KEY':settings.PUSHER_KEY}	
    if(request.method == 'GET'):
        form = AuthenticationForm()
		
		
        return render(request, 'landing.html', {'form': form})
		
    else:
        form = AuthenticationForm(request, data = request.POST)
		
        if form.is_valid():
            print("hiii")
            login(request, form.get_user())
            return redirect('/home/')
	#if form2.is_valid():
	#	new_user = form2.save()
	#	login(request, form2.get_user())
	#	return redirect('home')
			
        form = AuthenticationForm()
        return render(request, 'landing.html', {'form' : form})
def register_user(request):
    args = {}
    args.update(csrf(request))
    if request.method == 'POST':
        print("bii")
        form = UserCreationForm(request.POST)
        args['form'] = form
        print("kiii")
        if form.is_valid():
            print("wow")
            form.save()  # save user to database if form is valid
            print("hii")
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            
            salt = hashlib.sha1(str(random.random()).encode('utf-8')).hexdigest()[:5]   
            activation_key = hashlib.sha1((salt+email).encode('utf-8')).hexdigest()            
            key_expires = datetime.datetime.today() + datetime.timedelta(2)

            #Get user by username
            user=MyUser.objects.get(username=username)

            # Create and save user profile                                                                                                                                  
            new_profile = UserProfile(user=user, activation_key=activation_key, 
                key_expires=key_expires)
            new_profile.save()

            # Send email with activation key
            email_subject = 'Account confirmation'
            email_body = "Hey %s, thanks for signing up. To activate your account, click this link within \
            48hours http://127.0.0.1:8000/accounts/confirm/%s" % (username, activation_key)

            send_mail(email_subject, email_body, 'rkap95@gmail.com',
                [email], fail_silently=False)

            return HttpResponseRedirect('/user_profile/register_success')
    else:
        args['form'] = UserCreationForm()

    return render_to_response('landing.html', args, context_instance=RequestContext(request))
		

def register_confirm(request, activation_key):
    #check if user is already logged in and if he is redirect him to some other url, e.g. home
    if request.user.is_authenticated():
        HttpResponseRedirect('/home')

    # check if there is UserProfile which matches the activation key (if not then display 404)
    user_profile = get_object_or_404(UserProfile, activation_key=activation_key)

    #check if the activation key has expired, if it hase then render confirm_expired.html
    if user_profile.key_expires < timezone.now():
        return render_to_response('user_profile/confirm_expired.html')
    #if the key hasn't expired save user and set him as active and render some template to confirm activation
    user = user_profile.user
    user.is_active = True
    user.save()
    return render_to_response('user_profile/confirm.html')		

@login_required	
def register_success(request):
	data=Photo.objects.all()
	print(data[1].by)
	form3=photoForm()
	form2=commentForm()
	user=request.user
	return render(request,'home.html',{"item_list":data ,'form3' : form3,'form2' : form2,'user':user})

#ef register(request):
#if request.method == 'POST':
#	form2 = signupForm(request.POST)
#	if form2.is_valid():
#		new_user = form2.save()
			
#		return render(request,'home.html',{'user':new_user})
#else:
#	form3 = signupForm()
#return render(request, "login.html", {
	#'form3': form3,
 #  })
		

		
class commentForm(ModelForm):
	class Meta:
		model=Comment
		fields = '__all__'
		exclude = ['by','on','photo']
		
class signupForm(ModelForm):
	class Meta:
		model=MyUser
		fields = '__all__'
		exclude = ['profile_pic','following']
		
@login_required	
def home(request):
    data=Photo.objects.all()
    print(data[1].by)
    form3=photoForm()
    #comments=data.Comment_set.all()
    #print(comments)
    user=request.user
    obj=get_object_or_404(Comment,pk=1)
    return render(request,'home.html',{"item_list":data ,'form3' : form3,'user':user,'obj':obj})

@login_required
def friend_feed(request):
    friends = Friendship.objects.friends_for_user(request.user)
    data=[]
    for friend in friends:
        data+=Photo.objects.filter(by=friend)
    #comments=data.Comment_set.all()
    #print(comments)
    user=request.user
    obj=get_object_or_404(Comment,pk=1)
    return render(request,'home.html',{"item_list":data ,'user':user,'obj':obj})
    

@login_required
def mylogout(request):
    logout(request)
    return redirect('login')

	
	
@login_required
@require_http_methods(["GET"])
def autocomplete(request):
    print("kii")
    term = request.GET.get('term', '')
    print (term)
    if (term == ''):
        data = []
    else:
        print("hii")
        users = MyUser.objects.filter(username__icontains = term)
        #photo=Photo.objects.filter(hash_tags__icontains = term)
        data = [ {'label': user.get_full_name(), 'value' : user.id } for user in users ]
        print(data)
    return HttpResponse(json.dumps(data), content_type = 'application/json')                

"""	
@login_required
@require_http_methods(["GET"])
def tagsearch(request):
	term=request.GET.get('term', '')
	print(term)
	if(term == ''):
		photo_list=[]
	else:
		print("wow")
		searchash=HashTag.objects.filter(name=term)
		print(searchash)
		#photo_list=photo.objects.filter(hash_tags__name = term)
		#print(photo_list)
		
	return HttpResponse(json.dumps(data), content_type = 'application/json')        
	
	#return redirect(request,'home.html',{"item_list":photo_list})
"""
@login_required
@require_http_methods(["GET"])
def tagsearch(request):
    if 'q' in request.GET and request.GET['q']:
        q = request.GET['q']
        photo_list = Photo.objects.filter(hash_tags__name = q)
        if (photo_list):
            user=request.user
            return render(request, 'home.html',{"item_list":photo_list,"user":user})
        elif not photo_list:
            usersearch=get_object_or_404(MyUser,id=q)
            if(usersearch):
                profilepic=usersearch.profile_pic
                userphoto=Photo.objects.filter(by=request.user)
                return render(request,'profile.html',{'person':usersearch ,'profilepic':usersearch.profile_pic,'userphoto':userphoto})
        else:
            return HttpResponse('Please submit a search term.')
    else:
        return HttpResponse('Please submit a search term.')






		
@login_required
def profile(request):
    item = get_object_or_404(MyUser, id=request.user.id)
    #userinfo=get_object_or_404(UserInfo,id=request.user.id)
    if(item.profile_pic):
        profilepic=item.profile_pic
        form=userinfo_Form()
        userphoto=Photo.objects.filter(by=request.user)
        total=Photo.objects.filter(by=request.user).count()+Recipe.objects.filter(by=request.user).count()
        recipe=Recipe.objects.filter(by=request.user)
        data1=sorted(
    chain(userphoto, recipe),
    key=lambda instance: instance.on, reverse=True)[:3]
        data2=sorted(
    chain(userphoto, recipe),
    key=lambda instance: instance.points)[:3]
        userphoto=userphoto.filter(on__month=current_month)
        recipe=recipe.filter(on__month=current_month)
        data=chain(data1,data2)
        friendcount = len(Friendship.objects.friends_for_user(request.user))
        return render(request,'profile.html',{'person':item ,'profilepic':profilepic,'form':form,'userphoto':data,'total':total,'friendcount':friendcount,'user':item},)
    else:
        userphoto=Photo.objects.filter(by=request.user)
        recipe=Recipe.objects.filter(by=request.user)
        total=Photo.objects.filter(by=request.user).count()+Recipe.objects.filter(by=request.user).count()
        data1=sorted(
    chain(userphoto, recipe),
    key=lambda instance: instance.on, reverse=True)[:3]
        data2=sorted(
    chain(userphoto, recipe),
    key=lambda instance: instance.points)[:3]
        userphoto=userphoto.filter(on__month=current_month)
        recipe=recipe.filter(on__month=current_month)
        data=chain(data1,data2)
        form=userinfo_Form()
        friendcount = len(Friendship.objects.friends_for_user(request.user))
        return render(request,'profile.html',{'form':form,'userphoto':data,'person':item,'profilepic':1,'total':total,'friendcount':friendcount,'user':item})
	
@login_required
def addprofilepic(request):
	if request.method == 'POST':
		
		#form=profile_picForm(request.POST,request.FILES)
		user=get_object_or_404(MyUser, id=request.user.id)
		user.profile_pic=request.FILES.get('profile_pic')
		
		#print(form)
		
		
		
		#if form.is_valid():
		#	form.save();
			#return redirect('/thanku/')
		user.save()
	return redirect('/profile')

	
@login_required
def delprofilepic(request):
	#if request.method == 'POST'
		
		#form=profile_picForm(request.POST,request.FILES)
    user=get_object_or_404(MyUser, id=request.user.id)
    user.profile_pic=""
		
		#print(form)
		
		
		
		#if form.is_valid():
		#	form.save();
			#return redirect('/thanku/')
    user.save()
    return redirect('/profile')

@login_required
def addinfo(request):
    if request.method == 'POST':
        form=userinfo_Form(request.POST)
        print("hii")
        print(form)
        if form.is_valid():
            print("bii")
            if UserInfo.objects.filter(user=request.user).exists():
                new_info=form.save(commit=False)
                new_info.user = MyUser.objects.get(username=request.user.username)
                userinfo=get_object_or_404(UserInfo, user=request.user)
                userinfo.delete()
                new_info.save()
                return redirect('/profile/')
            else:    
                new_info=form.save(commit=False)
                new_info.user = MyUser.objects.get(username=request.user.username)
            #form_values = form.cleaned_data.get('liked_cuisine')
            #print(form_values)
                new_info.save()
                return redirect('/profile/')
        else:
            return HttpResponse()

@login_required
def edituserinfo(request):
    if request.method == 'POST':
        form=userinfo_Form(request.POST)
        if form.is_valid():
            new_info=form.save(commit=False)
            new_info.user = MyUser.objects.get(username=request.user.username)
            userinfo=get_object_or_404(UserInfo, user=request.user)
            userinfo.delete()
            new_info.save()
            return redirect('/profile/')
        
		
@login_required	
def show_user_id(request,user_id):
    try:
        user_id=int(user_id)
    except ValueError:
        raise Http404()
    friendcount = len(Friendship.objects.friends_for_user(request.user))
    total=Photo.objects.filter(by=request.user).count()+Recipe.objects.filter(by=request.user).count()
    item=get_object_or_404(MyUser,pk=user_id)
    if(item.profile_pic):
        profilepic=item.profile_pic
        userphoto=Photo.objects.filter(by=item)
        return render(request,'profile.html',{'person':item ,'profilepic':profilepic,'userphoto':userphoto,'friendcount':friendcount,'total':total})
    else:
        userphoto=Photo.objects.filter(by=item)
        return render(request,'profile.html',{'userphoto':userphoto,'person':item,'profilepic':1,'friendcount':friendcount,'total':total})
	#data=serializers.serialize("json",[user],indent=8)
	#return HttpResponse(data,content_type='application/json')	

@login_required
def show_feed(request):
    d = feedparser.parse('https://www.just-food.com/alerts/rssblog.aspx')
    return render(request,'feed.html',{"feed":d})