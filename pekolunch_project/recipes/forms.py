from typing import Any, Mapping
from django import forms
from django.core.files.base import File
from django.db.models.base import Model
from django.forms.utils import ErrorList
from .models import Recipe,RecipeFoodCategory
from choices import COOKING_TIME_CHOICES,COOKING_METHOD_CHOICES,MENU_CHOICES


class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(label='CSVファイル')

    def clean_csv_file(self):
        csv_file = self.cleaned_data['csv_file']
        # CSVファイルのバリデーションを追加する場合はここに記述
        return csv_file


class RecipeForm(forms.ModelForm):
    recipe_name = forms.CharField(label='レシピ名',max_length=32)
    menu_category = forms.ChoiceField(choices=MENU_CHOICES,label='カテゴリー')
    cooking_time_min = forms.ChoiceField(choices=COOKING_TIME_CHOICES,label='調理時間')
    cooking_method = forms.ChoiceField(choices=COOKING_METHOD_CHOICES,label='調理法')
    food_categories = forms.ModelMultipleChoiceField(queryset=RecipeFoodCategory.objects.all(),label='主な使用食材',required=False)
    image_url = forms.ImageField(label='画像',required=False)
    share = forms.BooleanField(label='全体にシェアする')
    is_avoid_main_dish = forms.BooleanField(label='主菜不要')
    average_evaluation = forms.FloatField(required=False,label='みんなの評価')
    
    
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['share'].initial = True
        self.fields['is_avoid_main_dish'].initial = False
    
    
    class Meta:
        model = Recipe
        fields = ['recipe_name','menu_category', 'cooking_time_min', 
                  'cooking_method', 'food_categories','image_url', 
                  'share','is_avoid_main_dish', 'average_evaluation']
       