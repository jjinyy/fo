from django.shortcuts import render
from django.http import JsonResponse
from .models import DimRegion, DimEducation, DimOccupation, DimTime, FactFoiMetrics, FactEoiMetrics

def index(request):
    return render(request, 'index.html')

def foi_api(request):
    region_id = request.GET.get('region', 'KR-11')
    edu_code = request.GET.get('edu', 'BA')
    time_id = request.GET.get('time', '2025Q4')
    row = FactFoiMetrics.objects.filter(
        region__region_id=region_id, edu__edu_code=edu_code, time__time_id=time_id
    ).first()
    if not row:
        return JsonResponse({"error": "not_found"}, status=404)
    return JsonResponse({
        "foi_score": float(row.foi_score or 0),
        "E": float(row.E_employ_norm or 0),
        "T": float(row.T_training_norm or 0),
        "I": float(row.I_infra_norm or 0),
    })

def eoi_api(request):
    occ_code = request.GET.get('occ', 'NCS-01')
    time_id = request.GET.get('time', '2025Q4')
    row = FactEoiMetrics.objects.filter(
        occ__occ_code=occ_code, time__time_id=time_id
    ).first()
    if not row:
        return JsonResponse({"error": "not_found"}, status=404)
    return JsonResponse({
        "eoi_base": float(row.eoi_score_base or 0),
        "W": float(row.W_wage_norm or 0),
        "S": float(row.S_stability_norm or 0),
        "G": float(row.G_growth_satis_norm or 0),
    })

def fgs_api(request):
    """간단 서버 계산 버전(선택): ?foi=84&eoi=83.2&loi=72.5"""
    try:
        foi = float(request.GET.get('foi', '0'))
        eoi = float(request.GET.get('eoi', '0'))
        loi = float(request.GET.get('loi', '0'))
        synergy = (foi * eoi) / 100.0
        fgs = 0.25*foi + 0.35*eoi + 0.25*synergy + 0.15*loi
        return JsonResponse({"fgs": fgs})
    except Exception:
        return JsonResponse({"error":"bad_parameters"}, status=400)
