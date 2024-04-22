from django.db import models
from accounts.models import Users
from django.utils import timezone

class MealPlan(models.Model):
    user = models.ForeignKey(Users,on_delete=models.CASCADE)
    staple_recipe = models.ForeignKey(Recipe,related_name='主食',on_delete=models.CASCADE)
    main_recipe = models.ForeignKey(Recipe,related_name='主菜',on_delete=models.CASCADE)
    side_recipe = models.ForeignKey(Recipe,related_name='副菜',on_delete=models.CASCADE)
    soup_recipe = models.ForeignKey(Recipe,related_name='汁物',on_delete=models.CASCADE)
    meal_date = models.DateField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    