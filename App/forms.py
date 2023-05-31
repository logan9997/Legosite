from django import forms

from config.config import EMAIL_LENGTH, PASSWORD_LENGTH, USERNAME_LENGTH


class ItemSelect(forms.Form):
    item_id_or_name = forms.CharField(max_length=100)


class AddItemToPortfolio(forms.Form):
    condition = forms.CharField(max_length=1)
    quantity = forms.IntegerField()
    bought_for = forms.FloatField()
    date_added = forms.DateField()


class PortfolioItemsSort(forms.Form):
    sort_field = forms.MultipleChoiceField(choices=(
        ('item_name', 'item_name'), ('condition', 'condition')
    ))
    field_order = forms.MultipleChoiceField(choices=(
        ('ASC', 'ASC'), ('DESC', 'DESC')
    ))


class LoginForm(forms.Form):
    username = forms.CharField(max_length=USERNAME_LENGTH)
    password = forms.CharField(max_length=PASSWORD_LENGTH)


class SignupFrom(forms.Form):
    email = forms.EmailField(max_length=EMAIL_LENGTH)
    username = forms.CharField(max_length=USERNAME_LENGTH)
    password = forms.CharField(max_length=PASSWORD_LENGTH)
    password_confirmation = forms.CharField(max_length=PASSWORD_LENGTH)


class AddOrRemovePortfolioItem(forms.Form):
    item_id = forms.CharField(max_length=700)
    remove_or_add = forms.CharField(max_length=1)
    condition = forms.MultipleChoiceField(choices=(
        ('N', 'N'), ('U', 'U')
    ))
    quantity = forms.IntegerField()


class ChangePassword(forms.Form):
    old_password = forms.CharField(max_length=PASSWORD_LENGTH)
    new_password = forms.CharField(max_length=PASSWORD_LENGTH)
    confirm_password = forms.CharField(max_length=PASSWORD_LENGTH)


class EmailPreferences(forms.Form):
    email = forms.CharField(max_length=EMAIL_LENGTH)
    preference = forms.MultipleChoiceField(choices=(
        ('Never', 'Never'), ('Occasional', 'Occasional'), ('All', 'All')
    ))


class PersonalInfo(forms.Form):
    username = forms.CharField(max_length=USERNAME_LENGTH)


class SearchSort(forms.Form):
    sort_field = forms.MultipleChoiceField(choices=(
        ('theme_name', 'theme_name'), ('popularity', 'popularity'),
        ('avg_growth', 'avg_growth'), ('num_items', 'num_items')
    ))
    order = forms.MultipleChoiceField(choices=(
        ('ASC', 'ASC'), ('DESC', 'DESC')
    ))
