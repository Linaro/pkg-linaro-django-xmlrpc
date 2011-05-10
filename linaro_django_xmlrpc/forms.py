from django import forms

class CreateTokenForm(forms.Form):
    
    description = forms.TextField(
    )
