import json
from datetime import datetime as dt
from datetime import timedelta

from django.shortcuts import redirect, render

from App.forms import LoginForm
from App.models import User
from config.config import MAX_LOGIN_ATTEMPTS, PASSWORD_LENGTH, USERNAME_LENGTH


def login(request):
    context = {
        "username_max_chars": USERNAME_LENGTH,
        "password_max_chars": PASSWORD_LENGTH
    }

    if request.session.get("user_id", -1) != -1:
        return redirect("index")

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            if "login_attempts" not in request.session:
                request.session["login_attempts"] = {}

            request.session["last_attempted_username"] = username

            if username not in request.session["login_attempts"]:
                request.session["login_attempts"][username] = {
                    "attempts": 0, "login_retry_date": -1}
                request.session.modified = True

            login_blocked = is_login_blocked(request, username)

            # check if username and password match, create new user_id session, del login_attempts session
            if (
                len(User.objects.filter(username=username, password=password)) == 1 and
                request.session["login_attempts"][username]["login_retry_date"] == -1
            ):
                user = User.objects.filter(
                    username=username, password=password)
                user_id = user.values_list("user_id", flat=True)[0]
                request.session["user_id"] = user_id
                del request.session["login_attempts"][username]
                return redirect("/")
            else:
                context.update(
                    {"login_message": "Username and Password do not match"})
                request.session["login_attempts"][username]["attempts"] += 1
                request.session.modified = True

    try:
        login_attempts = request.session["login_attempts"][username]["attempts"]
    except:
        try:
            login_attempts = request.session["login_attempts"]["last_attempted_username"]["attempts"]
        except:
            login_attempts = 0

    if login_attempts >= MAX_LOGIN_ATTEMPTS:
        if not login_blocked:
            tommorow = dt.strptime(
                str(dt.now() + timedelta(1)).split(".")[0], "%Y-%m-%d %H:%M:%S")
            request.session["login_attempts"][username]["login_retry_date"] = json.dumps(
                tommorow, default=str)

        login_retry_date = request.session["login_attempts"][username]["login_retry_date"]
        ''' ? EMAIL USER ? '''
        context.update({"login_message": [
                       "YOU HAVE ATTEMPTED LOGIN TOO MANY TIMES:", f"try again on {login_retry_date}"]})

    return render(request, "App/login.html", context=context)


def is_login_blocked(request, username):
    login_blocked = False
    if username in request.session.get("login_attempts") and request.session["login_attempts"][username]["login_retry_date"] != -1:
        login_retry_date = dt.strptime(
            request.session["login_attempts"][username]["login_retry_date"].strip('"'), '%Y-%m-%d %H:%M:%S')
        if dt.today() > login_retry_date:
            login_blocked = False
        else:
            login_blocked = True
    return login_blocked
