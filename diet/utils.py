import random
import re

from .models import DietPlan, DailyMealSlot, MealItem, FoodItem, DietProfile

DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

# DietProfile.goal  ->  FoodItem.goal_tags (naam alag hain! pehle match kabhi nahi hota tha)
GOAL_TAG = {'Weight Loss': 'Fat Loss', 'Muscle Gain': 'Muscle Gain', 'Maintenance': 'Maintenance'}

ACTIVITY_FACTOR = {
    'Sedentary': 1.2, 'Lightly Active': 1.375, 'Moderately Active': 1.55,
    'Very Active': 1.725, 'Super Active': 1.9,
    'Beginner': 1.375, 'Intermediate': 1.55, 'Advanced': 1.725,
}

# (slot, time, calorie share). Order = din ka asli order.
SLOT_SPLIT = [
    ('Breakfast', '08:00 AM', 0.25),
    ('Lunch', '01:00 PM', 0.35),
    ('Snack', '05:00 PM', 0.10),
    ('Dinner', '08:00 PM', 0.30),
]
MAX_ITEMS = {'Breakfast': 3, 'Lunch': 3, 'Dinner': 3, 'Snack': 2}

ALLERGEN_SYNONYMS = {
    'milk': ['milk', 'dairy', 'paneer', 'dahi', 'curd', 'ghee', 'lassi', 'chaas', 'butter', 'cheese', 'whey', 'doodh'],
    'dairy': ['milk', 'dairy', 'paneer', 'dahi', 'curd', 'ghee', 'lassi', 'chaas', 'butter', 'cheese', 'whey'],
    'lactose': ['milk', 'dairy', 'paneer', 'dahi', 'curd', 'lassi', 'chaas', 'cheese', 'whey'],
    'nuts': ['nut', 'almond', 'badam', 'cashew', 'kaju', 'peanut', 'moongfali', 'walnut', 'akhrot', 'pista'],
    'peanut': ['peanut', 'moongfali'],
    'egg': ['egg', 'anda', 'omelette', 'bhurji'],
    'gluten': ['gluten', 'wheat', 'atta', 'roti', 'paratha', 'bread', 'daliya', 'suji', 'rava', 'oats', 'toast'],
    'wheat': ['wheat', 'atta', 'roti', 'paratha', 'bread', 'daliya', 'suji', 'rava', 'gluten', 'toast'],
    'soy': ['soy', 'soya', 'tofu'],
    'fish': ['fish', 'machhli'],
    'shellfish': ['prawn', 'shrimp', 'crab', 'lobster'],
}


# ----------------------------------------------------------------------------
# Goal + targets
# ----------------------------------------------------------------------------
def map_goal(raw):
    """User.goal (free text, jaise 'Muscle Building') -> DietProfile.goal choice."""
    g = (raw or '').lower()
    if any(k in g for k in ('loss', 'fat', 'lean', 'cut', 'slim')):
        return 'Weight Loss'
    if any(k in g for k in ('endur', 'flex', 'mobil', 'hybrid', 'all-round')):
        return 'Maintenance'
    if any(k in g for k in ('muscle', 'bulk', 'gain', 'build', 'strength')):
        return 'Muscle Gain'
    return 'Maintenance'


def calculate_targets(user, goal):
    """
    Mifflin-St Jeor BMR x activity factor, phir goal adjust.
    Missing data ho to safe defaults. Returns dict(calories, protein, carbs, fats).
    """
    gender = (getattr(user, 'gender', '') or '').lower()
    male = gender.startswith('m')
    known_gender = gender.startswith('m') or gender.startswith('f')

    weight = getattr(user, 'weight', None) or (70 if male else 58)
    height = getattr(user, 'height', None) or (172 if male else 160)
    age = getattr(user, 'age', None) or 25

    offset = 5 if male else (-161 if known_gender else -78)
    bmr = 10 * weight + 6.25 * height - 5 * age + offset
    tdee = bmr * ACTIVITY_FACTOR.get(getattr(user, 'activity_level', '') or '', 1.4)

    if goal == 'Weight Loss':
        cal = tdee * 0.80
    elif goal == 'Muscle Gain':
        cal = tdee + 300
    else:
        cal = tdee

    floor = 1500 if male else 1200  # isse neeche mat jao (safety)
    cal = int(round(max(floor, min(cal, 4500)) / 10.0) * 10)

    per_kg = {'Weight Loss': 1.8, 'Muscle Gain': 2.0}.get(goal, 1.4)
    protein = int(round(min(weight * per_kg, cal * 0.35 / 4)))
    fats = int(round(cal * 0.25 / 9))
    carbs = max(0, int(round((cal - protein * 4 - fats * 9) / 4)))
    return {'calories': cal, 'protein': protein, 'carbs': carbs, 'fats': fats}


def calculate_target_calories(user, goal):
    """Purana naam (views.py me import hota hai). Ab personalized."""
    return calculate_targets(user, goal)['calories']


# ----------------------------------------------------------------------------
# Filters
# ----------------------------------------------------------------------------
def allowed_types_for(diet_type):
    return {
        'Non-Veg': ['Veg', 'Non-Veg', 'Egg', 'Vegan'],
        'Egg': ['Veg', 'Egg', 'Vegan'],
        'Veg': ['Veg', 'Vegan'],
        'Vegan': ['Vegan'],
    }.get(diet_type, [diet_type])


def expand_terms(terms):
    out = set()
    for t in terms or []:
        t = str(t).strip().lower()
        if not t:
            continue
        out.add(t)
        out.update(ALLERGEN_SYNONYMS.get(t, []))
    return out


def is_blocked(food, terms):
    """Food ke naam ya tags me allergy/dislike ka koi shabd (word-start par) mile to True."""
    if not terms:
        return False
    hay = ' '.join([food.name or '', ' '.join(food.tags or [])]).lower()
    return any(re.search(r'\b' + re.escape(t), hay) for t in terms)


def item_macros(item):
    """Ek MealItem ke total macros (quantity ke saath). Food delete ho gaya ho to snapshot."""
    q = item.quantity or 1.0
    food = None
    try:
        food = item.food_item
    except Exception:
        food = None
    if food is not None:
        try:
            return {
                'calories': (food.calories or 0) * q,
                'protein': (food.protein or 0) * q,
                'carbs': (food.carbs or 0) * q,
                'fats': (food.fats or 0) * q,
                'fiber': (food.fiber or 0) * q,
            }
        except Exception:
            pass
    return {
        'calories': float(item.calories_snapshot or 0),
        'protein': float(getattr(item, 'protein_snapshot', 0) or 0),
        'carbs': float(getattr(item, 'carbs_snapshot', 0) or 0),
        'fats': float(getattr(item, 'fats_snapshot', 0) or 0),
        'fiber': 0.0,
    }


def round_half(x):
    return round(x * 2) / 2.0


def make_meal_item(food, qty):
    return MealItem(
        food_item=food,
        quantity=qty,
        calories_snapshot=int(round((food.calories or 0) * qty)),
        protein_snapshot=round((food.protein or 0) * qty, 1),
        carbs_snapshot=round((food.carbs or 0) * qty, 1),
        fats_snapshot=round((food.fats or 0) * qty, 1),
    )


# ----------------------------------------------------------------------------
# Plan generation
# ----------------------------------------------------------------------------
def _make_scorer(profile):
    goal_tag = GOAL_TAG.get(profile.goal)

    def score(f):
        s = 0
        b = profile.budget_level
        if b == 'Low':
            s += {'Low': 10, 'Medium': 5}.get(f.budget, -5)
        elif b == 'Medium':
            s += {'Medium': 10, 'Low': 8}.get(f.budget, 0)
        else:
            s += 5
        if goal_tag and goal_tag in (f.goal_tags or []):
            s += 15
        p = f.protein or 0
        fib = f.fiber or 0
        if profile.goal == 'Muscle Gain':
            s += min(28, p * 1.4)
        elif profile.goal == 'Weight Loss':
            s += min(8, fib * 1.2) + min(20, p * 1.0)
        else:
            s += min(12, p * 0.6)
        return s

    return score


def _build_slot(name, time_label, budget, foods, scorer, use_count, yesterday_ids, used_today):
    """Calorie budget ke hisaab se 1 se 3 items chun kar quantity scale karta hai."""
    pool = [f for f in foods if name in (f.best_time or [])] or foods
    items = []
    chosen = set()
    remaining = float(budget)
    max_items = MAX_ITEMS.get(name, 2)

    for step in range(max_items):
        if remaining < max(60.0, budget * 0.12):
            break
        last = step == max_items - 1
        avail = [f for f in pool if f.id not in chosen and (f.calories or 0) > 0]
        fits = [f for f in avail if f.calories <= remaining * 1.25]
        cands = fits or avail
        if not cands:
            break

        def s(f):
            sc = scorer(f) - 8 * use_count.get(f.id, 0) + random.uniform(0, 6)
            if f.id in yesterday_ids:
                sc -= 15
            if f.id in used_today:
                sc -= 30
            return sc

        food = random.choice(sorted(cands, key=s, reverse=True)[:3])
        target = remaining if last else remaining * (0.6 if step == 0 else 0.7)
        qty = max(0.5, min(round_half(target / food.calories), 3.0 if last else 2.0))

        item = make_meal_item(food, qty)
        items.append(item)
        chosen.add(food.id)
        used_today.add(food.id)
        use_count[food.id] = use_count.get(food.id, 0) + 1
        remaining -= item.calories_snapshot

    if not items:  # koi bhi candidate na mile to kam se kam kuch to do
        food = random.choice(foods)
        items.append(make_meal_item(food, 1.0))
        use_count[food.id] = use_count.get(food.id, 0) + 1

    return DailyMealSlot(name=name, items=items, time=time_label)


def generate_new_plan(user):
    profile = DietProfile.objects(user=user).first()
    if not profile:
        return None

    blocked = expand_terms((profile.allergies or []) + (profile.dislikes or []))
    foods = [f for f in FoodItem.objects(type__in=allowed_types_for(profile.diet_type))
             if not is_blocked(f, blocked)]
    if not foods:
        return None

    target = profile.target_calories or 2000
    scorer = _make_scorer(profile)
    use_count = {}
    yesterday = {}
    days = {}

    for day in DAYS:
        used_today = set()
        slots = []
        for name, time_label, share in SLOT_SPLIT:
            slots.append(_build_slot(
                name, time_label, target * share, foods, scorer,
                use_count, yesterday.get(name, set()), used_today))
        yesterday = {
            s.name: {i.food_item.id for i in s.items if getattr(i, 'food_item', None) is not None}
            for s in slots
        }
        days[day] = slots

    plan = DietPlan(user=user, **days)
    plan.save()
    # Naya plan save hone ke BAAD purane deactivate karo (pehle plan kho jata tha agar generation fail ho)
    DietPlan.objects(user=user, id__ne=plan.id, is_active=True).update(set__is_active=False)
    return plan


def get_or_create_weekly_plan(user):
    active = DietPlan.objects(user=user, is_active=True).first()
    if active:
        return active
    return generate_new_plan(user)
