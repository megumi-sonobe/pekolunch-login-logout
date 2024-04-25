from django import forms
from .models import MealPlan
from bootstrap_datepicker_plus import DatePickerInput


class MealPlanForm(forms.ModelForm):
    class Meta:
        model = MealPlan
        fields = ['staple_recipe','main_recipe','side_recipe','soup_recipe','meal_date']
        widgets = {
            'meal_date':DatePickerInput(format='%Y-%m-%d')
        }
        