from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth  import authenticate,  login, logout
from .models import *
from django.contrib.auth.decorators import login_required
from .forms import ProfileForm, BlogPostForm
from django.views.generic import UpdateView
from django.contrib import messages
from django.db.models import Q
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.sites.shortcuts import get_current_site
from .utils import token_generator
from django.core.mail import EmailMessage


def blogs(request):
    posts = BlogPost.objects.all()
    posts = BlogPost.objects.filter().order_by('-dateTime')
    return render(request, "blog.html", {'posts':posts})

def blogs_comments(request, slug):
    post = BlogPost.objects.filter(slug=slug).first()
    comments = Comment.objects.filter(blog=post)
    if request.method=="POST":
        user = request.user
        content = request.POST.get('content','')
        blog_id =request.POST.get('blog_id','')
        comment = Comment(user = user, content = content, blog=post)
        comment.save()
    return render(request, "blog_comments.html", {'post':post, 'comments':comments})

def Delete_Blog_Post(request, slug):
    posts = BlogPost.objects.get(slug=slug)
    if request.method == "POST":
        posts.delete()
        return redirect('/')
    return render(request, 'delete_blog_post.html', {'posts':posts})

def search(request):
    if request.method == "POST":
        searched = request.POST['searched']
        blogs = BlogPost.objects.filter(Q(title__contains=searched) | Q(author__username__contains=searched))
        return render(request, "search.html", {'searched':searched, 'blogs':blogs})
    else:
        return render(request, "search.html", {})

@login_required(login_url = '/login')
def add_blogs(request):
    if request.method=="POST":
        form = BlogPostForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            blogpost = form.save(commit=False)
            blogpost.author = request.user
            blogpost.save()
            obj = form.instance
            alert = True
            return render(request, "add_blogs.html",{'obj':obj, 'alert':alert})
    else:
        form=BlogPostForm()
    return render(request, "add_blogs.html", {'form':form})

class UpdatePostView(UpdateView):
    model = BlogPost
    template_name = 'edit_blog_post.html'
    fields = ['title', 'slug', 'content', 'image']


def user_profile(request, myid):
    post = BlogPost.objects.filter(author=myid)
    return render(request, "user_profile.html", {'post':[post[0]]})

def ProfileInfo(request):
    posts = BlogPost.objects.filter(author = request.user)
    return render(request, "profile.html", {'posts' : posts})

def edit_profile(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile(user=request.user)
    if request.method=="POST":
        form = ProfileForm(data=request.POST, files=request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            alert = True
            return render(request, "edit_profile.html", {'alert':alert})
    else:
        form=ProfileForm(instance=profile)
    return render(request, "edit_profile.html", {'form':form})


def Register(request):
    if request.method=="POST":   
        username = request.POST['username']
        email = request.POST['email']
        first_name=request.POST['first_name']
        last_name=request.POST['last_name']
        password1 = request.POST['password1']
        mobileNum= request.POST['mobileNumber']

        user = User.objects.filter(Q(email = email) | Q(username = username))
        if user:
            return render(request, "register.html", {'alert': True})
        
        user = User.objects.create_user(username, email)
        user.set_password(password1)
        user.first_name = first_name
        user.last_name = last_name
        user.save()
        Profile.objects.create(user = user, phone_no = mobileNum)
        return render(request, 'login.html')   
    return render(request, "register.html")

def Login(request):
    alert = False
    if request.method=="POST":
        username = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, "Successfully Logged In")
            return redirect("/")
        else:
            alert = "incorrect" 
    return render(request, "login.html", {'message': alert})

def Logout(request):
    logout(request)
    messages.success(request, "Successfully logged out")
    return redirect('/login')

def ForgotPassword(request):
    return render(request, "forgot_password.html")

def SendEmail(request):
    if request.method == "POST":
        email = request.POST["email"]
        user = User.objects.filter(username = "user4").first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.id))
            domain = get_current_site(request).domain
            link = reverse('updatepass', kwargs={'uid': uid, 'token': token_generator.make_token(user)})
            activate_url = 'http://'+domain+link
            email_body = 'Hi '+ user.username +'! Please use this link to reset your password\n' + activate_url
            email = EmailMessage(
                'Reset Password for SenSen Blogs',  # subject
                email_body,
                'noreply@semycolon.com',  # from email address
                [email],  # to email address
            )
            email.send(fail_silently=False)
            messages.success(request, 'Account created for ' + user.username)
    return render(request, 'forgot_password.html', {'alert' : True})


def UpdatePass(request, uid, token):

    if request.method == "POST":
        password = request.POST["password"]
        confirmPassword = request.POST["confirmpassword"]
        if password != confirmPassword:
            return render(request, 'update_password.html', {'alert' : "The passwords don't match"})
        id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=id)
        user.set_password(password)
        user.save()
        return redirect('/login/')
    return render(request, 'update_password.html', {'uid' : uid, 'token' : token})