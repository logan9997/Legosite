from django.db.models import Q
from django.shortcuts import (
    redirect, 
    render
)

import os
import sys

from scripts.database import DatabaseManagment

from project_utils.item_format import Formatter
from project_utils.general import General 
from config.config import (
    USERNAME_LENGTH,
    EMAIL_LENGTH,
    PASSWORD_LENGTH
)

from App.models import (
    User
)

from App.forms import SignupFrom

GENERAL = General()
FORMATTER = Formatter()
DB = DatabaseManagment()

def join(request):

    context = {
        "username_max_chars":USERNAME_LENGTH,
        "email_max_chars":EMAIL_LENGTH,
        "password_max_chars":PASSWORD_LENGTH
    }

    if request.session.get("user_id", -1) != -1:
        return redirect("index")

    if request.method == 'POST':
        form = SignupFrom(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            password_confirmation = form.cleaned_data["password_confirmation"]
            
            if password == password_confirmation:

                if len(User.objects.filter(Q(username=username) | Q(email=email))) == 0:
                    new_user = User(
                        username=username,email=email,password=password,
                        email_preference="All", region="None"
                    )
                    new_user.save()

                    user = User.objects.filter(username=username, password=password)
                    user_id = user.values_list("user_id", flat=True)[0]
                    request.session["user_id"] = user_id
                    request.session.modified = True
                    return redirect("/")

            else:
                context["signup_message"] = "Passwords do not Match"
            
            if len(User.objects.filter(Q(username=username))) != 0:
                context["signup_message"] = "Username already exists"
            
            elif len(User.objects.filter(Q(email=email))) != 0:
                context["signup_message"] = "Email already exists"

        else:
            context["signup_message"] = get_login_error_message(form)
            
    return render(request, "App/join.html", context=context)


def get_login_error_message(form):
    error = str(form.errors)
    errors = list(filter(lambda x:x != "</ul>", error.split("</li>")))

    if "Enter a valid email address" in error:
        error_msg = "Invalid Email"

    elif "Ensure this value has at most" in error:
        max_chars = error.split("Ensure this value has at most ")[1].split(" characters")[0]
        field = error.split('<ul class="errorlist"><li>')[1]
        error_msg = f"{field.capitalize()} has a maximum length of {max_chars} characters."
    else:
        error_msg = "Please fill in all required fields (*)"
    return error_msg