from django import forms
from .models import MealPlan

class MealPlanForm(forms.Form):
    meal_date = forms.DateField(widget=forms.SelectDateWidget)

class MealPlanEditForm(forms.ModelForm):
    class Meta:
        model = MealPlan
        fields = ['staple_recipe', 'main_recipe', 'side_recipe', 'soup_recipe']
