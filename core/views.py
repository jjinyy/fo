from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Avg
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import logout
from django.views.decorators.http import require_http_methods
from django.shortcuts import redirect

from .models import (
    DimRegion, DimEducation, DimOccupation, DimTime,
    FactFoiMetrics, FactEoiMetrics,
    Assessment, Goal, Opportunity, Badge
)

def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard")   # 또는 "step1"
    return redirect("login")

# STEP 1: 기본정보
@login_required
def step1(request):
    # 기본값
    if request.method == "POST":
        request.session["basic"] = {
            "region": request.POST.get("region", "KR-11"),
            "edu": request.POST.get("edu", "BA"),
            "major": request.POST.get("major", ""),
            "occ": request.POST.get("occ", "NCS-01"),
            "salary": request.POST.get("salary", "4200"),
            "online_only": bool(request.POST.get("online_only")),
            "free_only": bool(request.POST.get("free_only")),
        }
        return redirect("step2")

    ctx = {
        "regions": DimRegion.objects.filter(region_level="sido", active_flag=True).order_by("region_name"),
        "edus": DimEducation.objects.order_by("order_no"),
        "occs": DimOccupation.objects.order_by("occ_name")[:200],
        "basic": request.session.get("basic", {"region":"KR-11","edu":"BA","occ":"NCS-01","salary":"4200"}),
    }
    return render(request, "core/steps/step1.html", ctx)

# STEP 2: LOI 설문
@login_required
def step2(request):
    if request.method == "POST":
        request.session["loi"] = {
            "wlb": float(request.POST.get("loi_wlb", 70)),
            "growth": float(request.POST.get("loi_growth", 80)),
            "sec": float(request.POST.get("loi_sec", 65)),
            "auto": float(request.POST.get("loi_auto", 75)),
            "goal": request.POST.get("loi_goal", "ACHIEVE"),
            "wa": float(request.POST.get("w_a", 0.3)),
            "wb": float(request.POST.get("w_b", 0.2)),
            "wc": float(request.POST.get("w_c", 0.3)),
            "wd": float(request.POST.get("w_d", 0.2)),
        }
        return redirect("step3")

    return render(request, "core/steps/step2.html", {"loi": request.session.get("loi", {})})

# STEP 3: 결과/추천
@login_required
def step3(request):
    basic = request.session.get("basic")
    loi = request.session.get("loi")
    if not basic or not loi:
        return redirect("step1")

    region_id = basic["region"]; edu_code = basic["edu"]; occ_code = basic["occ"]; time_id = "2025Q4"

    foi = FactFoiMetrics.objects.filter(region__region_id=region_id, edu__edu_code=edu_code, time__time_id=time_id).first()
    eoi = FactEoiMetrics.objects.filter(occ__occ_code=occ_code, time__time_id=time_id).first()

    foi_score = float(foi.foi_score) if foi and foi.foi_score is not None else 0.0
    W = float(eoi.W_wage_norm or 0); S = float(eoi.S_stability_norm or 0); G = float(eoi.G_growth_satis_norm or 0)

    loi_score = 0.3*loi["wlb"] + 0.3*loi["growth"] + 0.2*loi["sec"] + 0.2*loi["auto"]
    eoi_personal = loi["wa"]*W + loi["wb"]*S + loi["wc"]*G + loi["wd"]*loi_score
    synergy = (foi_score * eoi_personal) / 100.0
    fgs = 0.25*foi_score + 0.35*eoi_personal + 0.25*synergy + 0.15*loi_score

    ctx = {
        "basic": basic, "loi": loi,
        "foi": round(foi_score,1), "eoiP": round(eoi_personal,1),
        "loi_score": round(loi_score,1), "fgs": round(fgs,1),
    }
    return render(request, "core/steps/step3.html", {
        "basic": basic,
        "loi": loi,
        # 계산된 점수들도 함께 넘기는 중이면 그대로 유지
    })

# ===== 기존 API들 (그대로) =====
@login_required
def foi_api(request):
    region_id = request.GET.get('region', 'KR-11')
    edu_code = request.GET.get('edu', 'BA')
    time_id = request.GET.get('time', '2025Q4')
    row = FactFoiMetrics.objects.filter(region__region_id=region_id, edu__edu_code=edu_code, time__time_id=time_id).first()
    if not row:
        return JsonResponse({"error": "not_found"}, status=404)
    return JsonResponse({"foi_score": float(row.foi_score or 0),
                         "E": float(row.E_employ_norm or 0),
                         "T": float(row.T_training_norm or 0),
                         "I": float(row.I_infra_norm or 0)})

@login_required
def eoi_api(request):
    occ_code = request.GET.get('occ', 'NCS-01')
    time_id = request.GET.get('time', '2025Q4')
    row = FactEoiMetrics.objects.filter(occ__occ_code=occ_code, time__time_id=time_id).first()
    if not row:
        return JsonResponse({"error": "not_found"}, status=404)
    return JsonResponse({"eoi_base": float(row.eoi_score_base or 0),
                         "W": float(row.W_wage_norm or 0),
                         "S": float(row.S_stability_norm or 0),
                         "G": float(row.G_growth_satis_norm or 0)})

@login_required
def fgs_api(request):
    try:
        foi = float(request.GET.get('foi', '0'))
        eoi = float(request.GET.get('eoi', '0'))
        loi = float(request.GET.get('loi', '0'))
        synergy = (foi * eoi) / 100.0
        fgs = 0.25*foi + 0.35*eoi + 0.25*synergy + 0.15*loi
        return JsonResponse({"fgs": fgs})
    except Exception:
        return JsonResponse({"error":"bad_parameters"}, status=400)

@login_required
def save_assessment(request):
    """step3에서 계산된 session 값을 저장"""
    basic = request.session.get("basic")
    loi = request.session.get("loi")
    if not (basic and loi):
        messages.warning(request, "먼저 진단을 완료해주세요.")
        return redirect("step1")

    # step3 계산 로직을 재사용(중복 최소화)
    region_id = basic["region"]; edu_code = basic["edu"]; occ_code = basic["occ"]; time_id = "2025Q4"
    foi = FactFoiMetrics.objects.filter(region__region_id=region_id, edu__edu_code=edu_code, time__time_id=time_id).first()
    eoi = FactEoiMetrics.objects.filter(occ__occ_code=occ_code, time__time_id=time_id).first()

    foi_score = float(foi.foi_score) if foi and foi.foi_score is not None else 0.0
    W = float(eoi.W_wage_norm or 0); S = float(eoi.S_stability_norm or 0); G = float(eoi.G_growth_satis_norm or 0)

    loi_score = 0.3*float(loi["wlb"]) + 0.3*float(loi["growth"]) + 0.2*float(loi["sec"]) + 0.2*float(loi["auto"])
    eoi_personal = float(loi["wa"])*W + float(loi["wb"])*S + float(loi["wc"])*G + float(loi["wd"])*loi_score
    synergy = (foi_score * eoi_personal) / 100.0
    fgs = 0.25*foi_score + 0.35*eoi_personal + 0.25*synergy + 0.15*loi_score

    Assessment.objects.create(
        user=request.user,
        basic_json=basic, loi_json=loi,
        foi=round(foi_score,1), eoi_personal=round(eoi_personal,1),
        loi_score=round(loi_score,1), fgs=round(fgs,1)
    )
    messages.success(request, "진단 결과가 저장되었습니다.")
    return redirect("dashboard")

# --- 인증 ---
def login_view(request):
    if request.method == "POST":
        u = request.POST.get("username", "")
        p = request.POST.get("password", "")
        user = authenticate(request, username=u, password=p)
        if user:
            login(request, user)
            return redirect("dashboard")
        messages.error(request, "로그인 실패. 아이디/비밀번호를 확인하세요.")
    return render(request, "login.html")

def logout_view(request):
    logout(request)
    return redirect('login')

def signup_view(request):
    if request.method == "POST":
        u = request.POST.get("username","").strip()
        p = request.POST.get("password","").strip()
        if not u or not p:
            messages.error(request, "아이디/비밀번호를 입력하세요.")
        elif User.objects.filter(username=u).exists():
            messages.error(request, "이미 존재하는 아이디입니다.")
        else:
            User.objects.create_user(username=u, password=p)
            messages.success(request, "가입 완료! 로그인해주세요.")
            return redirect("login")
    return render(request, "signup.html")

@login_required
def recommend(request):
    user = request.user
    last = user.assessments.first()
    region = last.basic_json.get("region") if last else "KR-11"

    # 예시: 지역별 기회 카드 (나중에 공공데이터 API로 교체)
    recs = Opportunity.objects.filter(region=region)[:10]
    return render(request, "recommend.html", {"recs": recs})

@login_required
def cohort_view(request):
    avg_fgs = Assessment.objects.values("basic_json__region").annotate(avg_fgs=Avg("fgs"))
    return render(request, "cohort.html", {"avg_fgs": avg_fgs})

@login_required
def award_badges(user):
    total = user.assessments.count()
    if total == 1:
        Badge.objects.get_or_create(user=user, name="첫 진단 완료")
    elif total == 5:
        Badge.objects.get_or_create(user=user, name="꾸준한 진단자")
    elif user.goals.filter(is_completed=True).exists():
        Badge.objects.get_or_create(user=user, name="목표 달성자")

@login_required
def dashboard(request):
    last = Assessment.objects.filter(user=request.user).first()
    badges = Badge.objects.filter(user=request.user)[:6]
    return render(request, "dashboard.html", {"last": last, "badges": badges})

@login_required
def save_assessment(request):
    basic = request.session.get("basic")
    loi = request.session.get("loi")
    if not (basic and loi):
        messages.warning(request, "먼저 진단을 완료하세요.")
        return redirect("step1")

    region_id = basic["region"]; edu_code = basic["edu"]; occ_code = basic["occ"]; time_id = "2025Q4"
    foi = FactFoiMetrics.objects.filter(region__region_id=region_id, edu__edu_code=edu_code, time__time_id=time_id).first()
    eoi = FactEoiMetrics.objects.filter(occ__occ_code=occ_code, time__time_id=time_id).first()

    foi_score = float(foi.foi_score) if foi and foi.foi_score is not None else 0.0
    W = float(eoi.W_wage_norm or 0); S = float(eoi.S_stability_norm or 0); G = float(eoi.G_growth_satis_norm or 0)

    loi_score = 0.3*float(loi["wlb"]) + 0.3*float(loi["growth"]) + 0.2*float(loi["sec"]) + 0.2*float(loi["auto"])
    eoi_personal = float(loi["wa"])*W + float(loi["wb"])*S + float(loi["wc"])*G + float(loi["wd"])*loi_score
    synergy = (foi_score * eoi_personal)/100.0
    fgs = 0.25*foi_score + 0.35*eoi_personal + 0.25*synergy + 0.15*loi_score

    Assessment.objects.create(
        user=request.user, basic_json=basic, loi_json=loi,
        foi=round(foi_score,1), eoi_personal=round(eoi_personal,1),
        loi_score=round(loi_score,1), fgs=round(fgs,1)
    )
    award_badges(request.user)
    messages.success(request, "결과가 저장되었습니다.")
    return redirect("dashboard")

@login_required
def history(request):
    items = Assessment.objects.filter(user=request.user)
    return render(request, "core/history/history.html", {"items": items})

@login_required
def history_detail(request, pk):
    item = get_object_or_404(Assessment, pk=pk, user=request.user)
    return render(request, "core/history/history_detail.html", {"item": item})

# 목표 관리
@login_required
def goal_list(request):
    goals = Goal.objects.filter(user=request.user)
    return render(request, "core/goals/goal_list.html", {"goals": goals})

@login_required
def goal_create(request):
    if request.method == "POST":
        title = request.POST["title"].strip()
        target = float(request.POST["target"])
        due = request.POST["due"]
        last = request.user.assessments.first()
        start = last.fgs if last else 0
        Goal.objects.create(user=request.user, title=title, target_fgs=target, start_fgs=start, due_date=due)
        messages.success(request, "목표가 생성되었습니다.")
        return redirect("goal_list")
    return render(request, "core/goals/goal_create.html")

@login_required
def goal_detail(request, pk):
    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    if request.method == "POST" and "complete" in request.POST:
        goal.is_completed = True
        goal.save()
        award_badges(request.user)
        messages.success(request, "목표를 완료 처리했습니다.")
        return redirect("goal_detail", pk=pk)
    return render(request, "core/goals/goal_detail.html", {"goal": goal})

@login_required
def goal_complete(request, pk):
    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    goal.completed = True
    goal.save()
    return redirect("goal_list")
# 추천/코호트/정책
@login_required
def recommend(request):
    last = request.user.assessments.first()
    region = last.basic_json.get("region") if last else "KR-11"
    recs = Opportunity.objects.filter(region=region).order_by("-created_at")[:10]
    return render(request, "recommend.html", {"recs": recs})

@login_required
def cohort_view(request):
    avg_fgs = Assessment.objects.values("basic_json__region").annotate(avg_fgs=Avg("fgs")).order_by("basic_json__region")
    return render(request, "cohort.html", {"avg_fgs": avg_fgs})

from django.contrib.admin.views.decorators import staff_member_required
@staff_member_required
def policy_dashboard(request):
    regions = Assessment.objects.values("basic_json__region").annotate(
        avg_foi=Avg("foi"), avg_eoi=Avg("eoi_personal"), avg_fgs=Avg("fgs")
    ).order_by("basic_json__region")
    return render(request, "policy_dashboard.html", {"regions": regions})
