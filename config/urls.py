from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("admin/", admin.site.urls),

    # 인증 뷰
    path("login/",  auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    # 앱 라우트
    path("", include("core.urls")),   # core.urls 내부에서 ''(루트)를 대시보드/스텝으로 매핑
]
