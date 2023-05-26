from django.shortcuts import redirect, render

from App.forms import ChangePassword, EmailPreferences, PersonalInfo
from App.models import User

from config.config import PASSWORD_LENGTH, USERNAME_LENGTH


def settings(request):

    if 'user_id' not in request.session or request.session['user_id'] == -1:
        return redirect('index')
    user_id = request.session.get('user_id', -1)

    context = {
        'username': (User.objects.filter(user_id=user_id
            ).values_list('username', flat=True)[0]
        ),
        'email': (User.objects.filter(user_id=user_id
            ).values_list('email', flat=True)[0]
        ),
        'password_max_chars':PASSWORD_LENGTH,
        'username_max_chars':USERNAME_LENGTH,
    }

    # SETTINGS
    if request.method == 'POST':
        if request.POST.get('form-type') == 'change-password-form':
            form = ChangePassword(request.POST)
            if form.is_valid():
                old_password = form.cleaned_data['old_password']
                new_password = form.cleaned_data['new_password']
                confirm_password = form.cleaned_data['confirm_password']

                # list of rules that must all return True for the password to be updated, with corrisponding error messages
                # to be displayed to the user.
                rules: list[dict] = [
                    {
                        len(
                            User.objects.filter(
                            user_id=user_id, password=old_password)
                        ) > 0:
                    "'Old password' is incorrect"
                    },
                    {
                        new_password == confirm_password:
                        "'New password' and 'Confirm password' do not match"
                    },
                ]

                # add all dict keys to list, use all() method on list[bool] to see if all password change conditions are met
                if all([all(rule) for rule in rules]):
                    User.objects.filter(
                        password=old_password, user_id=user_id
                    ).update(password=new_password)
                else:
                    # pass an error message to context, based on what condition was not satisfied
                    context['change_password_error_message'] = get_change_password_error_message(rules)

        elif request.POST.get('form-type') == 'email-preference-form':
            form = EmailPreferences(request.POST)
            if form.is_valid():
                email = form.cleaned_data['email']
                preference = form.cleaned_data['preference'][0]
                
                User.objects.filter(user_id=user_id, email=email).update(
                    email_preference=preference
                )

        elif request.POST.get('form-type') == 'personal-details-form':
            form = PersonalInfo(request.POST)
            if form.is_valid():
                username = form.cleaned_data['username']
                if len(User.objects.filter(username=username)) == 0:
                    User.objects.filter(user_id=user_id).update(username=username)
                else:
                    context.update({'change_username_error_msg':'Username is taken'})

    return render(request, 'App/settings.html', context=context)


def get_change_password_error_message(rules: list[dict[str, str]]) -> str:
    for rule in rules:
        rule = rule.popitem()
        if not rule[0]:
            return rule[1]
