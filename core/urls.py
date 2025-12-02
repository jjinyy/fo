from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required

urlpatterns = [

    path("", views.home, name="home"),  # 루트 → 로그인/대시보드 분기
    path("dashboard/", login_required(views.dashboard), name="dashboard"),

    # 단계형 폼
    path("step1/", views.step1, name="step1"),
    path("step2/", views.step2, name="step2"),
    path("step3/", views.step3, name="step3"),

    # 대시보드 & 이력
    path("dashboard/", views.dashboard, name="dashboard"),
    path("save-assessment/", views.save_assessment, name="save_assessment"),
    path("history/", views.history, name="history"),
    path("history/<int:pk>/", views.history_detail, name="history_detail"),

    # 인증
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("signup/", views.signup_view, name="signup"),

    # API
    path("api/foi", views.foi_api, name="foi_api"),
    path("api/eoi", views.eoi_api, name="eoi_api"),
    path("api/fgs", views.fgs_api, name="fgs_api"),

    # 목표/성장관리
    path("goal/", views.goal_list, name="goal_list"),
    path("goal/new/", views.goal_create, name="goal_create"),
    path("goal/<int:pk>/", views.goal_detail, name="goal_detail"),
    path("goal/<int:pk>/complete/", views.goal_complete, name="goal_complete"),

    # 추천/코호트/정책
    path("recommend/", views.recommend, name="recommend"),
    path("cohort/", views.cohort_view, name="cohort"),
    path("policy/", views.policy_dashboard, name="policy_dashboard"),

]
