from typing import Any, Mapping
from django import forms
from django.core.files.base import File
from django.db.models.base import Model
from django.forms.utils import ErrorList
from .models import Recipe,RecipeFoodCategory,Process,Ingredient,FoodCategory
from choices import COOKING_TIME_CHOICES,COOKING_METHOD_CHOICES,MENU_CHOICES
from meal_planner.service import load_food_categories_from_csv
from typing import Tuple
import csv


class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(label='CSVファイル')

    def clean_csv_file(self):
        csv_file = self.cleaned_data['csv_file']
        # CSVファイルのバリデーションを追加する場合はここに記述
        return csv_file
    
    def load_food_categories(self):
        csv_file_path = self.cleaned_data['csv_file'].temporary_file_path()
        return load_food_categories_from_csv(csv_file_path)

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
    csv_file_path = None
    recipe_name = forms.CharField(label='レシピ名',max_length=32)
    menu_category = forms.ChoiceField(choices=MENU_CHOICES,label='カテゴリー')
    cooking_time_min = forms.ChoiceField(choices=COOKING_TIME_CHOICES,label='調理時間')
    cooking_method = forms.ChoiceField(choices=COOKING_METHOD_CHOICES,label='調理法')
    # food_categories = forms.ModelMultipleChoiceField(queryset=RecipeFoodCategory.objects.none(),label='主な使用食材',required=False)
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
    

    
    def __init__(self,*args,csv_file_path=None,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['average_evaluation'].widget = forms.HiddenInput()
        self.fields['share'].initial = True
        self.fields['is_avoid_main_dish'].initial = False
        
        if csv_file_path:
            food_categories = self.load_food_categories(csv_file_path)
            if food_categories:
                self.fields['food_categories'] = forms.ModelMultipleChoiceField(
                queryset=food_categories,
                label='主な使用食材',
                required=False,
                initial=food_categories,
                widget=forms.CheckboxSelectMultiple,
            )
                
    def load_food_categories(self,csv_file_path):
        food_categories = []
        with open(csv_file_path,newline='',encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)
            for row in reader:
                category_name = row[1].strip()
                if category_name:
                    food_categories.append(category_name)
        return FoodCategory.objects.filter(food_category_name_＿in=food_categories)
    
   
    def save(self,commit=True):
        recipe = super().save(commit=False)
        if commit:
            recipe.save()
            
            serving = self.cleaned_data.get('serving',1)
            recipe.adjust_ingredient_quantity_for_serving(serving)
            
            if RecipeForm.csv_file_path:
                process_description = self.cleaned_data.get('process_description')
                ingredient_name = self.cleaned_data.get('ingredient_name')
                process = Process.objects.create(recipe=recipe, description=process_description)
                ingredient = Ingredient.objects.create(recipe=recipe, ingredient_name=ingredient_name)
        return recipe,process,ingredient
    
    
