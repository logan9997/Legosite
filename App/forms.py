from django import forms

class ItemSelect(forms.Form):
    item_id = forms.CharField(max_length=20)


class AddItemToPortfolio(forms.Form):
    condition = forms.CharField(max_length=1)
    quantity = forms.IntegerField()
    bought_for = forms.FloatField()
    date_added = forms.DateField()


class PortfolioItemsSort(forms.Form):
    sort_field = forms.MultipleChoiceField(choices=(
        ("item_name", "item_name"), ("condition", "condition")
    ))
    field_order = forms.MultipleChoiceField(choices=(
        ("ASC", "ASC"), ("DESC", "DESC")
    ))


class LoginForm(forms.Form):
    username = forms.CharField(max_length=416)
    password = forms.CharField(max_length=142)


class SignupFrom(forms.Form):
    email = forms.CharField(max_length=60)
    username = forms.CharField(max_length=16)
    password = forms.CharField(max_length=22)
    password_confirmation = forms.CharField(max_length=22)


class AddOrRemovePortfolioItem(forms.Form):
    item_id = forms.CharField(max_length=700)
    remove_or_add = forms.CharField(max_length=1)
    condition = forms.MultipleChoiceField(choices=(
        ("N", "N"), ("U", "U")
    ))
    quantity = forms.IntegerField()


class ChangePassword(forms.Form):
    old_password = forms.CharField(max_length=22)
    new_password = forms.CharField(max_length=22)
    confirm_password = forms.CharField(max_length=22)


class EmailPreferences(forms.Form):
    email = forms.CharField(max_length=64)
    preference = forms.MultipleChoiceField(choices=(
        ("Never", "Never"), ("Occasional", "Occasional"), ("All", "All")
    ))


class PersonalInfo(forms.Form):
    username = forms.CharField(max_length=16)


class SearchSort(forms.Form):
    sort_field = forms.MultipleChoiceField(choices=(
        ("theme_name", "theme_name"), ("popularity", "popularity"),
        ("avg_growth", "avg_growth"), ("num_items", "num_items")
    )) 
    order = forms.MultipleChoiceField(choices=(
        ("ASC", "ASC"), ("DESC", "DESC")
    ))
