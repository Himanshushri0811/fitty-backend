import difflib
import logging
import re
import uuid
from datetime import datetime

from django.core.cache import cache
from mongoengine.errors import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DietProfile, FoodItem, DietPlan, MealItem, DailyDietLog, LoggedEntry
from .serializers import DietProfileSerializer, FoodItemSerializer, DietPlanSerializer
from .seed_data import FOODS
from .utils import (
    DAYS, calculate_targets, calculate_target_calories, get_or_create_weekly_plan,
    generate_new_plan, map_goal, allowed_types_for, expand_terms, is_blocked,
    item_macros, round_half,
)

logger = logging.getLogger(__name__)

MEAL_TYPES = ('Breakfast', 'Lunch', 'Dinner', 'Snack')
MAX_AI_PER_CAROUSEL = 2  # ek request me zyada se zyada itne foods ke liye AI call


# ============================================================================
# HELPERS
# ============================================================================
def get_ai_generator():
    from ai.services.food_generator import generate_food_persona
    return generate_food_persona


def _auth_user(request):
    user = getattr(request, 'user', None)
    if not user or not getattr(user, 'id', None):
        return None
    return user


def _parse_date(raw):
    try:
        return datetime.strptime(str(raw), '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return datetime.now().date()


def _num(value, lo, hi, default=0.0):
    try:
        v = float(value)
    except (TypeError, ValueError):
        return default
    if v != v:  # NaN
        return default
    return max(lo, min(hi, v))


def _norm(s):
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 ]', ' ', (s or '').lower())).strip()


def _truthy(v):
    return str(v).strip().lower() in ('1', 'true', 'yes')


def _rate_limited(user, key, limit, window=3600):
    """Simple per-user counter (Django cache). Cache fail ho to block nahi karte."""
    k = f'diet_rl:{key}:{user.id}'
    try:
        if cache.add(k, 1, window):
            return False
        try:
            n = cache.incr(k)
        except ValueError:
            cache.set(k, 1, window)
            n = 1
        return n > limit
    except Exception:
        return False


def _targets_from_profile(profile):
    cal = (profile.target_calories if profile else None) or 2000
    return {
        'calories': cal,
        'protein': (profile.target_protein if profile and profile.target_protein else int(cal * 0.30 / 4)),
        'carbs': (profile.target_carbs if profile and profile.target_carbs else int(cal * 0.40 / 4)),
        'fats': (profile.target_fats if profile and profile.target_fats else int(cal * 0.30 / 9)),
        'water': (profile.water_target if profile and profile.water_target else 8),
    }


def _get_log(user, date_str):
    log = DailyDietLog.objects(user=user, date=date_str).first()
    if not log:
        log = DailyDietLog(user=user, date=date_str)
    # Purane logs (jab sirf total_calories store hota tha) kho na jayein
    if not log.entries and log.total_calories and not log.legacy_calories:
        log.legacy_calories = log.total_calories
    return log


def _consumed(log):
    return {
        'calories': log.total_calories or 0,
        'protein': log.total_protein or 0,
        'carbs': log.total_carbs or 0,
        'fats': log.total_fats or 0,
        'fiber': log.total_fiber or 0,
        'water': log.water_intake or 0,
    }


def _entry_dict(e):
    return {
        'entry_id': e.entry_id,
        'ref': e.ref or '',
        'meal_type': e.meal_type,
        'time': e.time,
        'text': e.text,
        'items': list(e.items or []),
        'calories': round(e.calories or 0),
        'protein': round(e.protein or 0, 1),
        'carbs': round(e.carbs or 0, 1),
        'fats': round(e.fats or 0, 1),
        'source': e.source,
    }


def _sync_user_log(user, d, consumed_cal, water=None):
    """Dashboard (User.daily_calories_log) ko diet log ke saath same rakho. Fail ho to ignore."""
    try:
        from accounts.models import DailyCalorieLog
        target = None
        for entry in (user.daily_calories_log or []):
            ed = entry.date.date() if isinstance(entry.date, datetime) else entry.date
            if ed == d:
                target = entry
                break
        if target is None:
            target = DailyCalorieLog(date=d, calories_burned=0.0)
            user.daily_calories_log.append(target)
        target.calories_consumed = float(consumed_cal)
        if water is not None:
            target.water_intake_glasses = int(water)
        user.save()
    except Exception:
        logger.warning('user calorie log sync failed', exc_info=True)


def _save_log(user, log, d):
    log.recompute()
    log.save()
    _sync_user_log(user, d, log.total_calories, log.water_intake)


def _clean_items(detail):
    out = []
    if not isinstance(detail, list):
        return out
    for it in detail[:20]:
        if not isinstance(it, dict):
            continue
        out.append({
            'name': str(it.get('name') or '')[:60],
            'quantity': _num(it.get('quantity'), 0, 50, 1),
            'unit': str(it.get('unit') or '')[:20],
            'calories': round(_num(it.get('calories'), 0, 6000), 1),
            'protein': round(_num(it.get('protein'), 0, 500), 1),
            'carbs': round(_num(it.get('carbs'), 0, 800), 1),
            'fats': round(_num(it.get('fats'), 0, 500), 1),
            'source': str(it.get('source') or 'ai')[:10],
        })
    return out


def _default_meal_type():
    h = datetime.now().hour
    return 'Breakfast' if h < 11 else 'Lunch' if h < 16 else 'Snack' if h < 19 else 'Dinner'


# ============================================================================
# PROFILE
# ============================================================================
class DietProfileView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        user = _auth_user(request)
        if not user:
            return Response({"error": "Unauthorized"}, status=401)
        profile = DietProfile.objects(user=user).first()
        if not profile:
            return Response({"message": "Profile not setup"}, status=404)
        return Response(DietProfileSerializer(profile).data)

    def post(self, request):
        user = _auth_user(request)
        if not user:
            return Response({"error": "Unauthorized"}, status=401)

        data = request.data.dict() if hasattr(request.data, 'dict') else dict(request.data)
        profile = DietProfile.objects(user=user).first()

        goal = data.get('goal') or (profile.goal if profile else None) or map_goal(getattr(user, 'goal', ''))
        data['goal'] = goal

        # Targets: naye profile, goal change, ya explicit 'recalculate_targets' par hi dobara nikalo
        goal_changed = bool(profile) and profile.goal != goal
        need = (not profile) or goal_changed or _truthy(data.get('recalculate_targets')) \
            or (profile and not profile.target_protein)
        if need:
            t = calculate_targets(user, goal)
            if not data.get('target_calories'):
                data['target_calories'] = t['calories']
            for k in ('protein', 'carbs', 'fats'):
                if not data.get(f'target_{k}'):
                    data[f'target_{k}'] = t[k]

        if profile:
            before = self._snapshot(profile)
            serializer = DietProfileSerializer(profile, data=data, partial=True)
        else:
            before = None
            serializer = DietProfileSerializer(data=data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        try:
            if not profile:
                profile = serializer.save(user=user)
                get_or_create_weekly_plan(user)
            else:
                serializer.save()
                profile = DietProfile.objects(user=user).first()
                # Plan tabhi regenerate karo jab plan ko affect karne wali cheez badli ho
                if before != self._snapshot(profile):
                    generate_new_plan(user)
        except Exception as e:
            logger.error('Diet profile save failed', exc_info=True)
            return Response({"error": "Profile save nahi hua", "details": str(e)}, status=500)
        return Response(serializer.data)

    @staticmethod
    def _snapshot(p):
        return (
            p.goal, p.diet_type, p.budget_level,
            tuple(sorted(a.lower() for a in (p.allergies or []))),
            tuple(sorted(a.lower() for a in (p.dislikes or []))),
        )


# ============================================================================
# PLAN
# ============================================================================
class WeeklyPlanView(APIView):
    """GET /plan/  (?force=true => naya plan banao)"""
    permission_classes = [AllowAny]

    def get(self, request):
        user = _auth_user(request)
        if not user:
            return Response({"error": "Unauthorized"}, status=401)

        profile = DietProfile.objects(user=user).first()
        if not profile:
            return Response({"message": "Could not generate plan. Please ensure profile is set and foods exist."},
                            status=400)
        try:
            force = _truthy(request.query_params.get('force', 'false'))
            plan = generate_new_plan(user) if force else get_or_create_weekly_plan(user)
        except Exception as e:
            logger.error('Plan generation failed', exc_info=True)
            return Response({"message": "Plan generate nahi hua", "details": str(e)}, status=500)

        if not plan:
            return Response({"message": "Could not generate plan. Please ensure profile is set and foods exist."},
                            status=400)

        return Response({
            "plan": DietPlanSerializer(plan).data,
            "targets": _targets_from_profile(profile),
        })


# ============================================================================
# SEARCH / REPLACE
# ============================================================================
class FoodSearchView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        query = (request.query_params.get('q', '') or '').strip()[:60]
        if not query:
            return Response([])
        foods = FoodItem.objects(name__icontains=query).limit(10)
        return Response(FoodItemSerializer(foods, many=True).data)


class ReplaceMealView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user = _auth_user(request)
        if not user:
            return Response({"error": "Unauthorized"}, status=401)

        day = (request.data.get('day') or '').lower()
        period = request.data.get('period')
        try:
            index = int(request.data.get('index', 0))
        except (TypeError, ValueError):
            return Response({"error": "Invalid index"}, status=400)
        food_id = request.data.get('food_id')
        smart_option = request.data.get('replace_mode')

        profile = DietProfile.objects(user=user).first()
        plan = DietPlan.objects(user=user, is_active=True).first()
        if not plan or not profile:
            return Response({"error": "No active plan"}, status=404)
        if day not in DAYS:
            return Response({"error": "Invalid day"}, status=400)

        slot = next((s for s in getattr(plan, day) if s.name == period), None)
        if not slot:
            return Response({"error": "Meal slot not found"}, status=404)
        if index < 0 or index >= len(slot.items):
            return Response({"error": "Item index out of bounds"}, status=400)

        current = slot.items[index]
        current_cals = current.calories_snapshot or 0
        try:
            current_food_id = current.food_item.id if current.food_item else None
        except Exception:
            current_food_id = None

        food, reason, qty = None, "Manual replacement.", 1.0

        if food_id:
            try:
                food = FoodItem.objects(id=food_id).first()
            except ValidationError:
                food = None
        elif smart_option:
            blocked = expand_terms((profile.allergies or []) + (profile.dislikes or []))
            query = FoodItem.objects(type__in=allowed_types_for(profile.diet_type))
            pool = [f for f in query if f.id != current_food_id and not is_blocked(f, blocked)]
            cands = [f for f in pool if period in (f.best_time or [])] or pool
            if not cands:
                return Response({"error": "Koi suitable replacement nahi mila"}, status=404)

            if smart_option == 'high_protein':
                cands.sort(key=lambda x: (x.protein or 0) / max(x.calories or 1, 1), reverse=True)
                food = cands[0]
                reason = f"Switched to {food.name} for higher protein ({food.protein}g per serving)."
            elif smart_option == 'budget':
                order = {'Low': 3, 'Medium': 2, 'High': 1}
                cands.sort(key=lambda x: order.get(x.budget, 0), reverse=True)
                food = cands[0]
                reason = f"Switched to a wallet-friendly option ({food.budget} budget)."
            elif smart_option == 'fast':
                cands.sort(key=lambda x: x.prep_time or 999)
                food = cands[0]
                reason = f"Quick fix! {food.name} takes only {food.prep_time} mins to prep."
            else:  # similar
                cands.sort(key=lambda x: abs((x.calories or 0) - current_cals))
                food = cands[0]
                reason = f"Replaced with {food.name} as a calorie-matched alternative."

            # Din ka total na bigde: calories ke hisaab se quantity
            if food.calories:
                qty = max(0.5, min(round_half(current_cals / food.calories), 2.5)) if current_cals else 1.0

        if not food:
            return Response({"error": "Food not found or no smart match"}, status=404)

        from .utils import make_meal_item
        slot.items[index] = make_meal_item(food, qty)
        plan.save()

        return Response({
            "message": "Meal updated successfully",
            "new_food": food.name,
            "reason": reason,
            "quantity": qty,
            "calories": int(round((food.calories or 0) * qty)),
        })


# ============================================================================
# SEED (ADMIN ONLY)
# ============================================================================
class SeedFoodView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user = _auth_user(request)
        if not user or getattr(user, 'role', 'USER') != 'ADMIN':
            return Response({"error": "Admin access required"}, status=403)

        created = updated = 0
        for f in FOODS:
            doc = FoodItem.objects(name=f['name']).first()
            if not doc:
                FoodItem(**f).save()
                created += 1
                continue
            changed = False
            # Sirf khali fields bharo, purana curated data mat chhedo
            for k in ('best_time', 'goal_tags', 'tags'):
                if not getattr(doc, k) and f.get(k):
                    setattr(doc, k, f[k])
                    changed = True
            if not doc.fiber and f.get('fiber'):
                doc.fiber = f['fiber']
                changed = True
            if changed:
                doc.save()
                updated += 1
        return Response({"message": f"Seeded {created} foods, updated {updated}"})


# ============================================================================
# AI SMART BOX
# ============================================================================
class DietCarouselView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        user = _auth_user(request)
        if not user:
            return Response({"error": "Unauthorized"}, status=401)
        user_name = getattr(user, 'name', None) or "Friend"

        profile = DietProfile.objects(user=user).first()
        goal = profile.goal if profile else "Healthy"
        diet_type = profile.diet_type if profile else "Veg"
        allowed = allowed_types_for(diet_type)
        blocked = expand_terms(((profile.allergies or []) + (profile.dislikes or [])) if profile else [])

        if FoodItem.objects(type__in=allowed).count() < 10 and not _rate_limited(user, 'discover', 2, 3600):
            try:
                from ai.services.food_discovery import discover_new_foods
                discover_new_foods(goal, diet_type)
            except Exception:
                logger.warning('food discovery failed', exc_info=True)

        sample = list(FoodItem.objects.aggregate(
            {"$match": {"type": {"$in": allowed}}}, {"$sample": {"size": 15}}))

        gen_func = get_ai_generator()
        ai_budget = MAX_AI_PER_CAROUSEL if not _rate_limited(user, 'persona', 30, 3600) else 0
        results = []

        for row in sample:
            if len(results) >= 5:
                break
            doc = FoodItem.objects(id=row['_id']).first()
            if not doc or is_blocked(doc, blocked):
                continue

            persona = doc.ai_persona_text
            if not persona:
                if ai_budget > 0:
                    ai_budget -= 1
                    content = gen_func(doc.name, user_name, f"{doc.calories} cal, {doc.protein}g protein")
                    if content and not content.get('fallback'):
                        doc.ai_persona_text = content.get("persona_text", "")
                        doc.benefits = content.get("benefits", [])
                        doc.fitness_relevance = content.get("fitness_relevance", "")
                        if not doc.image_url:
                            doc.image_url = f"https://placehold.co/400x300?text={doc.name.replace(' ', '+')}"
                        doc.save()
                        persona = doc.ai_persona_text
                if not persona:  # AI nahi chala: temporary text, DB me SAVE nahi karte
                    persona = f"Namaste {user_name}, main {doc.name} hoon. {doc.calories} calories aur {doc.protein}g protein ke saath."

            results.append({
                "id": str(doc.id),
                "name": doc.name,
                "image_url": doc.image_url or f"https://placehold.co/400x300?text={doc.name.replace(' ', '+')}",
                "persona_text": persona,
                "fitness_relevance": doc.fitness_relevance or "",
                "benefits": doc.benefits or [],
                "macros": {"calories": doc.calories, "protein": doc.protein,
                           "carbs": doc.carbs, "fats": doc.fats},
            })
        return Response(results)


class DietFoodDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, id):
        try:
            food = FoodItem.objects(id=id).first()
        except ValidationError:
            food = None
        if not food:
            return Response({"error": "Not Found"}, status=404)

        ai_data = food.deep_dive_data or None  # cache
        if not ai_data:
            user = _auth_user(request)
            if user and _rate_limited(user, 'deepdive', 30, 3600):
                return Response({"error": "Thoda ruko, bahut zyada requests. Kuch der baad try karo."}, status=429)
            from ai.services.food_generator import generate_food_deep_dive
            ai_data = generate_food_deep_dive(food.name)
            if ai_data and not ai_data.get('fallback'):
                food.deep_dive_data = ai_data
                food.save()

        response_data = dict(FoodItemSerializer(food).data)
        response_data['deep_dive'] = ai_data

        img = response_data.get('image_url', "")
        if not img or "unsplash" in img:
            response_data['image_url'] = f"https://placehold.co/600x400/2a2a35/FFF?text={food.name.replace(' ', '+')}"
        return Response(response_data)


# ============================================================================
# NATURAL LANGUAGE LOGGER
# ============================================================================
def _match_food(name, lib):
    key = _norm(name)
    if not key:
        return None
    if key in lib:
        return lib[key]
    tokens = set(key.split())
    subset = [k for k in lib if tokens <= set(k.split())]
    if len(subset) == 1:
        return lib[subset[0]]
    close = difflib.get_close_matches(key, list(lib.keys()), n=1, cutoff=0.85)
    return lib[close[0]] if close else None


def _enrich_with_db(result):
    """AI ke estimates ko apne FoodItem DB se verify karo (DB ho to wahi sahi macros)."""
    detail = result.get('items_detail')
    if not isinstance(detail, list) or not detail:
        for k, hi in (('total_calories', 6000), ('total_protein', 500), ('total_carbs', 800), ('total_fats', 500)):
            result[k] = round(_num(result.get(k), 0, hi), 1)
        result.setdefault('items', [])
        return result

    lib = {_norm(f.name): f for f in FoodItem.objects()}
    lines = []
    for d in detail[:20]:
        if not isinstance(d, dict):
            continue
        name = str(d.get('name') or '').strip()[:60]
        if not name:
            continue
        qty = _num(d.get('quantity'), 0.1, 50, 1)
        line = {
            'name': name, 'quantity': qty, 'unit': str(d.get('unit') or '')[:20],
            'calories': _num(d.get('calories'), 0, 6000), 'protein': _num(d.get('protein'), 0, 500),
            'carbs': _num(d.get('carbs'), 0, 800), 'fats': _num(d.get('fats'), 0, 500),
            'fiber': _num(d.get('fiber'), 0, 200), 'source': 'ai',
        }
        match = _match_food(name, lib)
        if match and qty <= 10:
            line.update({
                'calories': match.calories * qty, 'protein': (match.protein or 0) * qty,
                'carbs': (match.carbs or 0) * qty, 'fats': (match.fats or 0) * qty,
                'fiber': (match.fiber or 0) * qty,
                'source': 'db', 'matched_name': match.name, 'food_id': str(match.id),
            })
        for k in ('calories', 'protein', 'carbs', 'fats', 'fiber'):
            line[k] = round(line[k], 1)
        lines.append(line)

    result['items_detail'] = lines
    result['items'] = [f"{l['quantity']:g} {l['name']}" for l in lines]
    result['total_calories'] = round(sum(l['calories'] for l in lines))
    result['total_protein'] = round(sum(l['protein'] for l in lines), 1)
    result['total_carbs'] = round(sum(l['carbs'] for l in lines), 1)
    result['total_fats'] = round(sum(l['fats'] for l in lines), 1)
    return result


class CalculateMacrosView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user = _auth_user(request)
        if not user:
            return Response({"error": "Unauthorized"}, status=401)
        text = (request.data.get('text') or '').strip()
        if not text:
            return Response({"error": "Text is required"}, status=400)
        if len(text) > 300:
            return Response({"error": "Text bahut lamba hai (max 300 characters)"}, status=400)
        if _rate_limited(user, 'macros', 30, 3600):
            return Response({"error": "Bahut zyada requests. Thodi der baad try karo."}, status=429)

        from ai.services.food_generator import calculate_macros_from_text
        result = calculate_macros_from_text(text)
        if not isinstance(result, dict) or "error" in result:
            return Response(result if isinstance(result, dict) else {"error": "AI unavailable"}, status=503)
        return Response(_enrich_with_db(result))


# ============================================================================
# LOGGING (single source of truth: DailyDietLog.entries)
# ============================================================================
class LogFoodView(APIView):
    """
    POST /log-food/
    {date, items[], totals{total_calories,total_protein,total_carbs,total_fats},
     items_detail[], meal_type, client_id, source}
    """
    permission_classes = [AllowAny]

    def post(self, request):
        user = _auth_user(request)
        if not user:
            return Response({"error": "Unauthorized"}, status=401)

        d = request.data
        items = d.get('items') or []
        if not items:
            return Response({"error": "No items to log"}, status=400)

        day = _parse_date(d.get('date'))
        date_str = day.strftime('%Y-%m-%d')
        totals = d.get('totals') or {}
        log = _get_log(user, date_str)

        client_id = str(d.get('client_id') or '')[:64]
        if client_id:
            dup = next((e for e in log.entries if e.client_id == client_id), None)
            if dup:  # double click / retry
                return Response({"message": "Already logged", "new_total": log.total_calories,
                                 "entry_id": dup.entry_id, "consumed": _consumed(log)})

        names = [(i.get('name') if isinstance(i, dict) else str(i))[:80] for i in items[:20]]
        meal_type = d.get('meal_type') if d.get('meal_type') in MEAL_TYPES else _default_meal_type()
        entry = LoggedEntry(
            entry_id=uuid.uuid4().hex,
            client_id=client_id or None,
            meal_type=meal_type,
            time=datetime.now().strftime('%I:%M %p'),
            text=', '.join(names)[:300],
            items=_clean_items(d.get('items_detail')),
            calories=_num(totals.get('total_calories', totals.get('calories')), 0, 6000),
            protein=_num(totals.get('total_protein', totals.get('protein')), 0, 500),
            carbs=_num(totals.get('total_carbs', totals.get('carbs')), 0, 800),
            fats=_num(totals.get('total_fats', totals.get('fats')), 0, 500),
            source=str(d.get('source') or 'ai')[:10],
        )
        log.entries.append(entry)
        try:
            _save_log(user, log, day)
        except Exception as e:
            logger.error('Log save failed', exc_info=True)
            return Response({"error": "Log save nahi hua", "details": str(e)}, status=500)

        return Response({"message": "Logged successfully", "new_total": log.total_calories,
                         "entry_id": entry.entry_id, "consumed": _consumed(log)})


class RemoveLogEntryView(APIView):
    """POST /log-food/remove/  {date, entry_id}"""
    permission_classes = [AllowAny]

    def post(self, request):
        user = _auth_user(request)
        if not user:
            return Response({"error": "Unauthorized"}, status=401)
        day = _parse_date(request.data.get('date'))
        log = _get_log(user, day.strftime('%Y-%m-%d'))
        entry_id = request.data.get('entry_id')
        before = len(log.entries)
        log.entries = [e for e in log.entries if e.entry_id != entry_id]
        if len(log.entries) == before:
            return Response({"error": "Entry not found"}, status=404)
        _save_log(user, log, day)
        return Response({"message": "Removed", "consumed": _consumed(log)})


class MarkMealEatenView(APIView):
    """POST /mark-eaten/  {date, period, eaten?}  (eaten na do to toggle)"""
    permission_classes = [AllowAny]

    def post(self, request):
        user = _auth_user(request)
        if not user:
            return Response({"error": "Unauthorized"}, status=401)

        day = _parse_date(request.data.get('date'))
        period = request.data.get('period')
        plan = DietPlan.objects(user=user, is_active=True).first()
        if not plan:
            return Response({"error": "No active plan"}, status=404)
        slot = next((s for s in getattr(plan, DAYS[day.weekday()]) if s.name == period), None)
        if not slot:
            return Response({"error": "Meal slot not found"}, status=404)

        log = _get_log(user, day.strftime('%Y-%m-%d'))
        ref = f'plan:{period}'
        existing = next((e for e in log.entries if e.ref == ref), None)
        eaten = request.data.get('eaten')
        eaten = (existing is None) if eaten is None else bool(eaten)

        if eaten and not existing:
            tot = {'calories': 0.0, 'protein': 0.0, 'carbs': 0.0, 'fats': 0.0, 'fiber': 0.0}
            names = []
            for it in slot.items:
                m = item_macros(it)
                for k in tot:
                    tot[k] += m[k]
                try:
                    names.append(it.food_item.name if it.food_item else (it.custom_name or 'Item'))
                except Exception:
                    names.append(it.custom_name or 'Item')
            log.entries.append(LoggedEntry(
                entry_id=uuid.uuid4().hex, ref=ref,
                meal_type=period if period in MEAL_TYPES else 'Snack',
                time=datetime.now().strftime('%I:%M %p'),
                text=', '.join(names)[:300], source='plan',
                calories=tot['calories'], protein=tot['protein'], carbs=tot['carbs'],
                fats=tot['fats'], fiber=tot['fiber'],
            ))
        elif not eaten and existing:
            log.entries = [e for e in log.entries if e.ref != ref]

        _save_log(user, log, day)
        return Response({"eaten": eaten, "period": period, "new_total": log.total_calories,
                         "consumed": _consumed(log)})


class WaterLogView(APIView):
    """POST /water/  {date, glasses} (absolute) ya {date, delta}"""
    permission_classes = [AllowAny]

    def post(self, request):
        user = _auth_user(request)
        if not user:
            return Response({"error": "Unauthorized"}, status=401)
        day = _parse_date(request.data.get('date'))
        log = _get_log(user, day.strftime('%Y-%m-%d'))
        if 'glasses' in request.data:
            val = int(_num(request.data.get('glasses'), 0, 30, 0))
        else:
            val = (log.water_intake or 0) + int(_num(request.data.get('delta'), -30, 30, 1))
        log.water_intake = max(0, min(30, val))
        _save_log(user, log, day)
        profile = DietProfile.objects(user=user).first()
        return Response({"water": log.water_intake, "target": (profile.water_target if profile else 8) or 8})


class DailySummaryView(APIView):
    """
    GET /daily-summary/?date=YYYY-MM-DD   (date = user ka LOCAL date)
    Ek hi jagah se: targets, asli consumed, remaining, aaj ke entries, aaj ke planned meals (eaten flag ke saath).
    """
    permission_classes = [AllowAny]

    def get(self, request):
        user = _auth_user(request)
        if not user:
            return Response({"error": "Unauthorized"}, status=401)

        day = _parse_date(request.query_params.get('date'))
        date_str = day.strftime('%Y-%m-%d')
        profile = DietProfile.objects(user=user).first()
        targets = _targets_from_profile(profile)
        log = _get_log(user, date_str)
        consumed = _consumed(log)

        eaten_refs = {e.ref for e in log.entries if e.ref}
        planned = []
        plan = DietPlan.objects(user=user, is_active=True).first()
        if plan:
            for slot in getattr(plan, DAYS[day.weekday()]):
                if slot.name == 'Extras':  # purana bug: logs plan me 'Extras' ban ke aate the
                    continue
                cal = prot = 0.0
                for it in slot.items:
                    m = item_macros(it)
                    cal += m['calories']
                    prot += m['protein']
                planned.append({
                    'name': slot.name, 'time': slot.time,
                    'is_eaten': f'plan:{slot.name}' in eaten_refs,
                    'calories': round(cal), 'protein': round(prot, 1),
                })

        def pct(a, b):
            return round(min(999, (a / b) * 100)) if b else 0

        return Response({
            'date': date_str,
            'targets': targets,
            'consumed': consumed,
            'remaining': {
                'calories': max(0, targets['calories'] - consumed['calories']),
                'protein': max(0, round(targets['protein'] - consumed['protein'], 1)),
                'carbs': max(0, round(targets['carbs'] - consumed['carbs'], 1)),
                'fats': max(0, round(targets['fats'] - consumed['fats'], 1)),
                'water': max(0, targets['water'] - consumed['water']),
            },
            'percent': {
                'calories': pct(consumed['calories'], targets['calories']),
                'protein': pct(consumed['protein'], targets['protein']),
                'carbs': pct(consumed['carbs'], targets['carbs']),
                'fats': pct(consumed['fats'], targets['fats']),
                'water': pct(consumed['water'], targets['water']),
            },
            'entries': [_entry_dict(e) for e in log.entries],
            'planned_today': planned,
        })
