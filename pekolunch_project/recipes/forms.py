from typing import Any, Mapping
from django import forms
from django.core.files.base import File
from django.db.models.base import Model
from django.forms.utils import ErrorList
from .models import Recipe,RecipeFoodCategory,Process,Ingredient
from choices import COOKING_TIME_CHOICES,COOKING_METHOD_CHOICES,MENU_CHOICES


class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(label='CSVファイル')

    def clean_csv_file(self):
        csv_file = self.cleaned_data['csv_file']
        # CSVファイルのバリデーションを追加する場合はここに記述
        return csv_file
    
class ProcessForm(forms.ModelForm):
    class Meta:
        model = Process
        fields = ['process_number','description']
        
class IngredientForm(forms.ModelForm):
    person_quantity = forms.IntegerField(label='',min_value=1)
    
    class Meta:
        model = Ingredient
        fields = ['ingredient_name','quantity_unit']
        
    def save(self,commit=True):
        ingredient = super().save(commit=False)
        if commit:
            ingredient.save()
            
            person_quantity = self.cleaned_data.get('person_quantity',1)
            ingredient.adjust_quantity_for_person(person_quantity)
            
        return ingredient        


class RecipeForm(forms.ModelForm):
    recipe_name = forms.CharField(label='レシピ名',max_length=32)
    menu_category = forms.ChoiceField(choices=MENU_CHOICES,label='カテゴリー')
    cooking_time_min = forms.ChoiceField(choices=COOKING_TIME_CHOICES,label='調理時間')
    cooking_method = forms.ChoiceField(choices=COOKING_METHOD_CHOICES,label='調理法')
    food_categories = forms.ModelMultipleChoiceField(queryset=RecipeFoodCategory.objects.all(),label='主な使用食材',required=False)
    image_url = forms.ImageField(label='画像',required=False)
    serving = forms.IntegerField(label='人分',min_value=1)
    share = forms.BooleanField(label='全体にシェアする')
    is_avoid_main_dish = forms.BooleanField(label='主菜不要')
    # average_evaluation = forms.FloatField(required=False,label='みんなの評価')
    process_form = ProcessForm()
    ingredient_form = IngredientForm()
    
    process_description = forms.CharField(label='作り方',widget=forms.Textarea)
    ingredient_name = forms.CharField(label='材料',max_length=64)
    
    
    class Meta:
        model = Recipe
        fields = ['recipe_name','menu_category', 'cooking_time_min', 
                  'cooking_method', 'food_categories','image_url', 
                  'share','is_avoid_main_dish', 'average_evaluation']
    

    
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['average_evaluation'].widget = forms.HiddenInput()
        self.fields['share'].initial = True
        self.fields['is_avoid_main_dish'].initial = False
    
   
    def save(self,commit=True):
        recipe = super().save(commit=False)
        if commit:
            recipe.save()
            
            serving = self.cleaned_data.get('serving',1)
            recipe.adjust_ingredient_quantity_for_serving(serving)
            
            
        process_description = self.cleaned_data.get('process_description')
        ingredient_name = self.cleaned_data.get('ingredient_name')
        
        Process.objects.create(recipe=recipe, description=process_description)
        Ingredient.objects.create(recipe=recipe, ingredient_name=ingredient_name)

    
        return recipe
    
    
