from config.config import EMAIL_LENGTH, PASSWORD_LENGTH, USERNAME_LENGTH
from django.db.models import Q
from django.shortcuts import redirect, render
from project_utils.general import General

from App.forms import SignupFrom
from App.models import User

GENERAL = General()

def join(request):

    context = {
        'username_max_chars': USERNAME_LENGTH,
        'email_max_chars': EMAIL_LENGTH,
        'password_max_chars': PASSWORD_LENGTH
    }

    if request.session.get('user_id', -1) != -1:
        return redirect('index')

    if request.method == 'POST':
        form = SignupFrom(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            password_confirmation = form.cleaned_data['password_confirmation']

            if password == password_confirmation:

                if len(User.objects.filter(Q(username=username) | Q(email=email))) == 0:
                    new_user = User(
                        username=username, email=email, password=password,
                        email_preference='All', region='None'
                    )
                    new_user.save()

                    user_id = User.objects.filter(
                        username=username, password=password
                    ).values_list('user_id', flat=True)[0]

                    request.session['user_id'] = user_id
                    request.session.modified = True
                    return redirect('/')

            else:
                context['signup_message'] = 'Passwords do not Match'

            if len(User.objects.filter(Q(username=username))) != 0:
                context['signup_message'] = 'Username already exists'

            elif len(User.objects.filter(Q(email=email))) != 0:
                context['signup_message'] = 'Email already exists'

        else:
            context['signup_message'] = GENERAL.get_login_error_message(form)

    return render(request, 'App/join.html', context=context)



