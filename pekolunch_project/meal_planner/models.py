from django.db import models
from accounts.models import Users
from django.utils import timezone
from recipes.models import Recipe

class MealPlan(models.Model):
    user = models.ForeignKey(Users,on_delete=models.CASCADE)
    staple_recipe = models.ForeignKey(Recipe,related_name='主食',on_delete=models.SET_NULL, null=True)
    main_recipe = models.ForeignKey(Recipe,related_name='主菜',on_delete=models.SET_NULL, null=True)
    side_recipe = models.ForeignKey(Recipe,related_name='副菜',on_delete=models.SET_NULL, null=True)
    soup_recipe = models.ForeignKey(Recipe,related_name='汁物',on_delete=models.SET_NULL, null=True)
    meal_date = models.DateField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
   
    def __str__(self):
        return f"{self.user.username}'s Meal Plan - {self.meal_date}"

    