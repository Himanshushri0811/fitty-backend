"""
diet/seed_data.py
Approximate nutrition per standard serving (ghar ka khana, IFCT/USDA ke aas-paas).
Isse plan generator ko best_time + goal_tags + allergen tags milte hain.
"""
B, L, D, S = 'Breakfast', 'Lunch', 'Dinner', 'Snack'
FL, MG, MT, KT, EN = 'Fat Loss', 'Muscle Gain', 'Maintenance', 'Keto', 'Energy'


def _f(name, serving, type_, kcal, p, c, f, fiber, budget, best, goals, prep=15,
       cuisine='Indian', tags=None):
    return {
        'name': name, 'serving_unit': serving, 'type': type_, 'calories': kcal,
        'protein': p, 'carbs': c, 'fats': f, 'fiber': fiber, 'budget': budget,
        'best_time': best, 'goal_tags': goals, 'prep_time': prep,
        'cuisine': cuisine, 'tags': tags or [],
    }


FOODS = [
    # ---- Breakfast ----
    _f('Oats Upma', '1 bowl', 'Vegan', 250, 8, 40, 5, 5, 'Low', [B], [FL, MT], 15, tags=['oats', 'gluten']),
    _f('Poha', '1 plate', 'Vegan', 270, 5, 50, 7, 3, 'Low', [B, S], [MT, EN], 15, tags=['rice']),
    _f('Paneer Bhurji', '150g', 'Veg', 300, 18, 5, 22, 1, 'Medium', [B, D], [MG, KT], 15, tags=['milk', 'dairy', 'paneer']),
    _f('Besan Chilla', '2 pieces', 'Vegan', 220, 12, 25, 8, 4, 'Low', [B], [FL, MG], 15, tags=['gram flour']),
    _f('Moong Dal Chilla', '2 pieces', 'Vegan', 200, 14, 26, 4, 5, 'Low', [B], [FL], 15, tags=['moong']),
    _f('Idli Sambar', '3 idli with sambar', 'Vegan', 245, 9, 45, 3, 4, 'Low', [B], [FL, MT], 20, 'South Indian', ['rice', 'lentil']),
    _f('Vegetable Daliya', '1 bowl', 'Vegan', 220, 7, 40, 4, 6, 'Low', [B], [FL, MT], 20, tags=['wheat', 'gluten']),
    _f('Aloo Paratha', '1 piece', 'Vegan', 300, 7, 42, 12, 3, 'Low', [B], [EN, MT], 20, tags=['wheat', 'gluten', 'potato']),
    _f('Masala Omelette', '2 eggs', 'Egg', 210, 13, 3, 16, 1, 'Low', [B], [MG, KT], 10, tags=['egg']),
    _f('Egg Bhurji', '2 eggs', 'Egg', 220, 14, 3, 17, 1, 'Low', [B, D], [MG, KT], 10, tags=['egg']),
    _f('Boiled Eggs', '2 large', 'Egg', 140, 12, 1, 10, 0, 'Low', [B, S], [MG, FL, KT], 10, 'Global', ['egg']),
    _f('Peanut Butter Toast', '2 slices', 'Vegan', 300, 12, 32, 15, 5, 'Medium', [B], [MG, EN], 5, 'Global', ['peanut', 'nuts', 'gluten', 'bread']),
    _f('Dahi', '1 katori', 'Veg', 60, 3.5, 5, 3, 0, 'Low', [B, L, S], [FL, MT], 2, tags=['milk', 'dairy', 'curd']),
    # ---- Lunch / Dinner ----
    _f('Dal Tadka', '1 bowl', 'Veg', 180, 10, 25, 6, 6, 'Low', [L, D], [FL, MG, MT], 25, tags=['lentil', 'ghee']),
    _f('Rajma Masala', '1 bowl', 'Veg', 230, 11, 33, 6, 8, 'Low', [L, D], [MG, MT], 40, tags=['kidney beans']),
    _f('Chana Masala', '1 bowl', 'Vegan', 250, 12, 36, 7, 9, 'Low', [L, D], [FL, MG], 35, tags=['chickpea']),
    _f('Palak Paneer', '1 bowl', 'Veg', 280, 16, 9, 20, 3, 'Medium', [L, D], [MG, KT], 25, tags=['milk', 'dairy', 'paneer']),
    _f('Mixed Veg Sabzi', '1 bowl', 'Vegan', 120, 3, 14, 6, 4, 'Low', [L, D], [FL, MT], 20, tags=['vegetables']),
    _f('Chicken Curry', '1 bowl', 'Non-Veg', 350, 30, 10, 15, 2, 'Medium', [L, D], [MG], 40, tags=['chicken']),
    _f('Grilled Chicken Breast', '150g', 'Non-Veg', 250, 46, 0, 5, 0, 'Medium', [L, D], [MG, FL, KT], 20, 'Global', ['chicken']),
    _f('Grilled Fish', '1 fillet', 'Non-Veg', 220, 25, 0, 10, 0, 'Medium', [L, D], [FL, MG, KT], 20, 'Global', ['fish']),
    _f('Egg Curry', '2 eggs with gravy', 'Egg', 280, 15, 8, 21, 2, 'Low', [L, D], [MG], 25, tags=['egg']),
    _f('Soya Chunks Curry', '1 bowl', 'Vegan', 220, 24, 14, 6, 6, 'Low', [L, D], [MG, FL], 20, tags=['soy']),
    _f('Roti', '1 piece', 'Vegan', 100, 3, 20, 1, 3, 'Low', [L, D], [MT, EN], 10, tags=['wheat', 'gluten']),
    _f('Brown Rice', '1 cup cooked', 'Vegan', 210, 5, 44, 2, 3, 'Low', [L, D], [MT, EN], 25, 'Global', ['rice']),
    _f('Steamed Rice', '1 cup cooked', 'Vegan', 205, 4, 45, 0.4, 1, 'Low', [L, D], [MT, EN], 20, tags=['rice']),
    _f('Veg Pulao', '1 plate', 'Vegan', 300, 7, 52, 8, 3, 'Low', [L], [MT, EN], 25, tags=['rice']),
    _f('Moong Dal Khichdi', '1 bowl', 'Veg', 250, 9, 42, 5, 4, 'Low', [L, D], [MT, FL], 25, tags=['rice', 'lentil', 'ghee']),
    _f('Tofu Stir Fry', '1 bowl', 'Vegan', 200, 17, 8, 12, 3, 'Medium', [L, D], [MG, FL, KT], 15, 'Global', ['soy', 'tofu']),
    _f('Cucumber Tomato Salad', '1 bowl', 'Vegan', 60, 2, 12, 1, 3, 'Low', [L, D, S], [FL], 5, tags=['salad']),
    _f('Paneer Tikka', '6 pieces', 'Veg', 250, 18, 7, 17, 1, 'Medium', [S, D], [MG, KT], 25, tags=['milk', 'dairy', 'paneer']),
    # ---- Snacks ----
    _f('Roasted Chana', '1 katori', 'Vegan', 150, 8, 24, 3, 7, 'Low', [S], [FL, MG], 2, tags=['chickpea']),
    _f('Sprouts Salad', '1 bowl', 'Vegan', 150, 10, 25, 1, 6, 'Low', [S, B], [FL, MG], 10, tags=['sprouts', 'moong']),
    _f('Almonds', '10 pieces', 'Vegan', 70, 2.5, 2.5, 6, 1.5, 'Medium', [S], [MG, KT, EN], 1, 'Global', ['almond', 'nuts']),
    _f('Roasted Peanuts', '30g', 'Vegan', 170, 7.5, 5, 14, 2.5, 'Low', [S], [MG, EN], 1, tags=['peanut', 'nuts']),
    _f('Apple', '1 medium', 'Vegan', 95, 0.5, 25, 0.3, 4.4, 'Low', [S, B], [FL, EN], 1, 'Global', ['fruit']),
    _f('Banana', '1 medium', 'Vegan', 105, 1.3, 27, 0.4, 3, 'Low', [S, B], [EN, MG], 1, 'Global', ['fruit']),
    _f('Chaas', '1 glass', 'Veg', 40, 2, 5, 1, 0, 'Low', [S, L], [FL, MT], 2, tags=['milk', 'dairy', 'buttermilk']),
    _f('Roasted Makhana', '1 bowl', 'Vegan', 110, 3.5, 20, 1, 2, 'Low', [S], [FL, MT], 5, tags=['lotus seeds']),
    _f('Milk', '1 glass', 'Veg', 150, 8, 12, 8, 0, 'Low', [B, S], [MG, MT], 2, tags=['milk', 'dairy']),
    _f('Whey Protein Shake', '1 scoop with water', 'Veg', 120, 24, 3, 1.5, 0, 'High', [S, B], [MG, FL], 2, 'Global', ['milk', 'whey', 'dairy']),
]
