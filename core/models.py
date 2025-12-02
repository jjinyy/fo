from django.db import models
from django.conf import settings

class DimRegion(models.Model):
    region_id = models.CharField(primary_key=True, max_length=16)
    region_name = models.CharField(max_length=100)
    region_level = models.CharField(max_length=16)  # 'sido'/'sigungu'
    parent_region = models.ForeignKey('self', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='children')
    iso_code = models.CharField(max_length=16, blank=True, null=True)
    active_flag = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self): return f"{self.region_name}({self.region_id})"

class DimEducation(models.Model):
    edu_code = models.CharField(primary_key=True, max_length=10)  # HS/AD/BA/MSPHD
    edu_name = models.CharField(max_length=50)
    order_no = models.IntegerField()
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self): return self.edu_code

class DimOccupation(models.Model):
    occ_code = models.CharField(primary_key=True, max_length=32)
    occ_name = models.CharField(max_length=100)
    industry_code = models.CharField(max_length=32, blank=True, null=True)
    parent_occ = models.ForeignKey('self', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='sub')
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self): return self.occ_code

class DimTime(models.Model):
    time_id = models.CharField(primary_key=True, max_length=16) # '2025Q4'
    year = models.IntegerField()
    quarter = models.IntegerField()
    month = models.IntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self): return self.time_id

class FactFoiMetrics(models.Model):
    region = models.ForeignKey(DimRegion, on_delete=models.CASCADE)
    edu = models.ForeignKey(DimEducation, on_delete=models.CASCADE)
    time = models.ForeignKey(DimTime, on_delete=models.CASCADE)
    foi_score = models.DecimalField(max_digits=6, decimal_places=3, null=True)
    E_employ_norm = models.DecimalField(max_digits=6, decimal_places=3, null=True)
    T_training_norm = models.DecimalField(max_digits=6, decimal_places=3, null=True)
    I_infra_norm = models.DecimalField(max_digits=6, decimal_places=3, null=True)
    source_version = models.CharField(max_length=32, default="v1.0")
    data_quality_flag = models.CharField(max_length=8, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = ('region','edu','time')

class FactEoiMetrics(models.Model):
    occ = models.ForeignKey(DimOccupation, on_delete=models.CASCADE)
    time = models.ForeignKey(DimTime, on_delete=models.CASCADE)
    eoi_score_base = models.DecimalField(max_digits=6, decimal_places=3, null=True)
    W_wage_norm = models.DecimalField(max_digits=6, decimal_places=3, null=True)
    S_stability_norm = models.DecimalField(max_digits=6, decimal_places=3, null=True)
    G_growth_satis_norm = models.DecimalField(max_digits=6, decimal_places=3, null=True)
    source_version = models.CharField(max_length=32, default="v1.0")
    data_quality_flag = models.CharField(max_length=8, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = ('occ','time')

class Assessment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assessments")
    created_at = models.DateTimeField(auto_now_add=True)

    # 입력 스냅샷 (간단히 텍스트/JSON)
    basic_json = models.JSONField(default=dict)  # region/edu/occ/salary/online_only/free_only
    loi_json   = models.JSONField(default=dict)  # wlb/growth/sec/auto/goal/wa/wb/wc/wd

    # 결과 스냅샷
    foi = models.FloatField(default=0)
    eoi_personal = models.FloatField(default=0)
    loi_score = models.FloatField(default=0)
    fgs = models.FloatField(default=0)

    class Meta:
        ordering = ["-created_at"]

class Goal(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="goals")
    title = models.CharField(max_length=200)
    target_fgs = models.FloatField()
    start_fgs = models.FloatField(default=0)
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)

    def progress(self):
        last = self.user.assessments.first()
        if not last:
            return 0
        delta = last.fgs - self.start_fgs
        total = self.target_fgs - self.start_fgs
        return max(0, min(100, (delta / total) * 100)) if total > 0 else 0

class Opportunity(models.Model):
    title = models.CharField(max_length=200)
    region = models.CharField(max_length=50)   # 예: KR-11
    link = models.URLField()
    category = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)  # ← 추가


class Badge(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="badges")
    name = models.CharField(max_length=100)
    awarded_at = models.DateTimeField(auto_now_add=True)
