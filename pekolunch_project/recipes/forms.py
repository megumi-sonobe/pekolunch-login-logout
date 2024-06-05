from typing import Any, Mapping
from django import forms
from django.core.files.base import File
from django.db.models.base import Model
from django.forms.utils import ErrorList
from .models import Recipe, RecipeFoodCategory, Process, Ingredient, FoodCategory, UserEvaluation
from choices import COOKING_TIME_CHOICES, COOKING_METHOD_CHOICES, MENU_CHOICES


class ProcessForm(forms.ModelForm):
    description = forms.CharField(label='説明', max_length=255)

    class Meta:
        model = Process
        fields = ['process_number', 'description']
        labels = {
            'process_number': '手順',
        }
        widgets = {
            'process_number': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].label = ''

    def save(self, commit=True):
        process = super().save(commit=False)
        if not process.pk and self.instance.recipe_id: 
            last_process = Process.objects.filter(recipe=self.instance.recipe).order_by('-process_number').first()
            if last_process:
                process.process_number = last_process.process_number + 1
            else:
                process.process_number = 1
        if commit:
            process.save()
        return process


class IngredientForm(forms.ModelForm):
    # 分量・単位のフィールドを追加
    quantity_unit = forms.CharField(max_length=32, label='分量・単位')

    class Meta:
        model = Ingredient
        fields = ['ingredient_name', 'quantity_unit']
        labels = {
            'ingredient_name': '材料名',
            'quantity_unit': '分量・単位',
        }

    def save(self, commit=True):
        ingredient = super().save(commit=False)
        ingredient_name = self.cleaned_data['ingredient_name']
        quantity_unit = self.cleaned_data['quantity_unit']

        if ingredient_name and quantity_unit:  # 材料名と分量が入力されていることを確認
            ingredient.ingredient_name = ingredient_name
            ingredient.quantity_unit = quantity_unit

            if commit:
                ingredient.save()

        return ingredient


class RecipeForm(forms.ModelForm):
    recipe_name = forms.CharField(label='レシピ名', max_length=32)
    menu_category = forms.ChoiceField(choices=MENU_CHOICES, label='カテゴリー')
    cooking_time_min = forms.ChoiceField(choices=COOKING_TIME_CHOICES, label='調理時間')
    cooking_method = forms.ChoiceField(choices=COOKING_METHOD_CHOICES, label='調理法')
    image_url = forms.ImageField(label='画像', required=False)
    serving = forms.IntegerField(label='', min_value=1)
    share = forms.BooleanField(label='全体にシェアする', required=False)
    is_avoid_main_dish = forms.BooleanField(label='主菜不要', required=False)

    class Meta:
        model = Recipe
        fields = ['recipe_name', 'menu_category', 'cooking_time_min',
                  'cooking_method', 'image_url', 'serving', 'share',
                  'is_avoid_main_dish', 'average_evaluation']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['average_evaluation'].widget = forms.HiddenInput()
        if self.instance and self.instance.pk:
            self.fields['share'].initial = bool(self.instance.share)
            self.fields['is_avoid_main_dish'].initial = bool(self.instance.is_avoid_main_dish)
            self.initial['serving'] = self.instance.serving
        else:
            self.fields['share'].initial = True
            self.fields['is_avoid_main_dish'].initial = False
            self.initial['serving'] = 1

        # データベースからフードカテゴリーを取得
        food_categories_qs = FoodCategory.objects.all()

        self.fields['food_categories'] = forms.ModelMultipleChoiceField(
            queryset=food_categories_qs,
            label='主な使用食材（5つまで選択）:',
            required=False,
            initial=[],
            widget=forms.CheckboxSelectMultiple,
        )

    def clean_food_categories(self):
        food_categories = self.cleaned_data.get('food_categories')
        if not food_categories:
            raise forms.ValidationError('主な使用食材を1つ以上選択してください。')
        if len(food_categories) > 5:
            raise forms.ValidationError('5つまで選択できます。')
        return food_categories

    def clean_recipe_name(self):
        recipe_name = self.cleaned_data.get('recipe_name')
        if Recipe.objects.filter(recipe_name=recipe_name).exists():
            raise forms.ValidationError("このレシピ名は既に存在します。別の名前を選んでください。")
        return recipe_name
    
    def clean_menu_category(self):
        menu_category = self.cleaned_data.get('menu_category')
        if menu_category is None:
            raise forms.ValidationError('カテゴリーを選択してください。')
        return menu_category

    def clean_cooking_time_min(self):
        cooking_time_min = self.cleaned_data.get('cooking_time_min')
        if cooking_time_min is None:
            raise forms.ValidationError('調理時間を選択してください。')
        return cooking_time_min

    def clean_cooking_method(self):
        cooking_method = self.cleaned_data.get('cooking_method')
        if cooking_method is None:
            raise forms.ValidationError('調理法を選択してください。')
        return cooking_method

    def save(self, commit=True):
        recipe = super().save(commit=False)
        recipe.share = int(self.cleaned_data['share'])  # Booleanからintに変換して保存
        recipe.is_avoid_main_dish = int(self.cleaned_data['is_avoid_main_dish'])  # Booleanからintに変換して保存
        if commit:
            recipe.save()
            food_categories = self.cleaned_data.get('food_categories')
            if food_categories:
                recipe.food_categories.set(food_categories)
                print(f"Selected Food Categories: {food_categories}")  # デバッグ用
            recipe.save()
        return recipe


class UserEvaluationForm(forms.ModelForm):
    class Meta:
        model = UserEvaluation
        fields = ['evaluation']
