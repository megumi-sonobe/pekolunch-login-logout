from typing import Iterable
from django.db import models
from django.utils import timezone
from choices import COOKING_TIME_CHOICES,COOKING_METHOD_CHOICES,MENU_CHOICES
from accounts.models import Users
from django.db.models import Avg


    
class FoodCategory(models.Model):
    food_category_name = models.CharField(max_length=32)
    
    def __str__(self):
        return self.food_category_name

class Recipe(models.Model):
    food_categories = models.ManyToManyField(FoodCategory,through='RecipeFoodCategory')
    recipe_name = models.CharField(max_length=32)
    menu_category = models.IntegerField(choices=MENU_CHOICES)
    cooking_time_min = models.IntegerField(choices=COOKING_TIME_CHOICES,null=False)
    cooking_method = models.IntegerField(choices=COOKING_METHOD_CHOICES,null=False)
    image_url = models.ImageField(upload_to='recipes/images/',null=True,blank=True)
    share = models.IntegerField(default=1)
    is_avoid_main_dish = models.IntegerField(default=0)
    average_evaluation = models.FloatField(null=True,blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.recipe_name
    
    def update_average_rating(self):
        #レシピ平均評価を更新
        average_rating = self.user_evaluation_set.aggregate(Avg('evaluation'))['evaluation__avg']
        if average_rating is not None:
            self.average_evaluation = round(average_rating,2)
        else:
            self.average_evaluation = None
        self.save()
        
    def adjust_ingredient_quantity_for_serving(self,serving,is_child=False):
        ingredients = self.ingredient_set.all()
        for ingredient in ingredients:
            if is_child:
                serving *= 0.5
                
            ingredient.quantity_unit = f"{serving * ingredient.quantity_unit}"
            ingredient.save()
        

    

class RecipeFoodCategory(models.Model):
    food_category = models.ForeignKey(FoodCategory,on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe,on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('food_category','recipe')
        
    
    
class Process(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    process_number = models.IntegerField(unique=True)
    description = models.CharField(max_length=255)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
        
class Ingredient(models.Model):
    recipe = models.ForeignKey(Recipe,on_delete=models.CASCADE)
    ingredient_name = models.CharField(max_length=64,null=False)
    quantity_unit = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def adjust_quantity_for_serving(self,serving):
        quantity, unit = self.quantity_unit.split(' ',1)
        if serving != 0:
            self.quantity_unit = f"{float(quantity) / serving} {unit}"
        self.save()
        
    
class UserEvaluation(models.Model):
    user = models.ForeignKey(Users,on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe,on_delete=models.CASCADE,related_name='user_evaluations')
    evaluation =models.IntegerField(choices=[(0,'1 star'),(1,'2 star'),(2,'3 star')])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args,**kwargs):
        super().save(*args,**kwargs)
        self.recipe.update_average_rating()
        