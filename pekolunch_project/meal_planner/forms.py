from django import forms
from .models import MealPlan


class MealPlanForm(forms.ModelForm):
    meal_date = forms.DateField(widget=forms.DateInput(attrs={'type':'date'}))

    class Meta:
        model = MealPlan
        fields = ['staple_recipe', 'main_recipe', 'side_recipe', 'soup_recipe', 'meal_date']
