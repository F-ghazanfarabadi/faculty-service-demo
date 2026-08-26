# -*- coding: utf-8 -*-
"""
ماژول امتیازدهی جدید:

معیار 1: Safety (ایمنی)
  - هیچ تأثیری بر ایمنی ندارد: 1
  - ممکن است در آینده باعث مشکل ایمنی شود: 5
  - در حال حاضر خطر ایمنی ایجاد می‌کند: 7
  - خطر ایمنی جدی و فوری ایجاد می‌کند: 9

معیار 2: Class_Disruption (اختلال در کلاس)
  - خیر، هیچ اختلالی ایجاد نکرده: 1
  - اختلال جزئی ایجاد کرده: 3
  - اختلال قابل توجه ایجاد کرده: 5
  - برگزاری کلاس را مختل یا متوقف کرده: 9

معیار 3: Infrastructure_Criticality (بحرانی‌بودن خدمت)
  - خدمت غیر بحرانی (نظافت، تزئین و تجمیل): 1
  - خدمت نسبتاً بحرانی (نظام‌های کمکی): 5
  - خدمت بسیار بحرانی (برق، آب، تأسیسات اساسی): 8
  - خدمت حیاتی (سیستم‌های فوری، ایمنی): 10

ضریب زمانی (Waiting Time Multiplier):
  - هر روز تاخیر افزایش میدهد
  - فرمول: multiplier = 1 + 0.1 * days_delayed
  - مثال: 1 روز = 1.1، 3 روز = 1.3، 10 روز = 2.0
"""

from datetime import datetime

# ---- معیار ۱: Safety (ایمنی) ----
SAFETY_OPTIONS = {
    "هیچ تأثیری بر ایمنی ندارد": 1,
    "ممکن است در آینده باعث مشکل ایمنی شود": 5,
    "در حال حاضر خطر ایمنی ایجاد می‌کند": 7,
    "خطر ایمنی جدی و فوری ایجاد می‌کند": 9,
}

# ---- معیار ۲: Class_Disruption (اختلال در کلاس) ----
CLASS_DISRUPTION_OPTIONS = {
    "خیر، هیچ اختلالی ایجاد نکرده": 1,
    "اختلال جزئی ایجاد کرده": 3,
    "اختلال قابل توجه ایجاد کرده": 5,
    "برگزاری کلاس را مختل یا متوقف کرده": 9,
}

# ---- معیار ۳: Infrastructure_Criticality (بحرانی‌بودن خدمت) ----
INFRASTRUCTURE_OPTIONS = {
    "خدمت غیر بحرانی (نظافت، تزئین و تجمیل)": 1,
    "خدمت نسبتاً بحرانی (نظام‌های کمکی)": 5,
    "خدمت بسیار بحرانی (برق، آب، تأسیسات اساسی)": 8,
    "خدمت حیاتی (سیستم‌های فوری، ایمنی)": 10,
}

# دسته‌بندی خدمات (برای تخصیص به کارکنان)
CATEGORY_OPTIONS = ["برق", "تأسیسات", "نظافت", "عمومی"]


def compute_waiting_time_multiplier(timestamp_str: str, now: datetime = None) -> float:
    """
    محاسبه ضریب زمانی بر اساس روزهای سپری‌شده
    
    فرمول: multiplier = 1 + 0.1 * days_delayed
    - روز 0: 1.0×
    - روز 1: 1.1×
    - روز 3: 1.3×
    - روز 5: 1.5×
    - روز 10: 2.0×
    
    این ضریب در محاسبه Priority Score **ضرب** میشود
    """
    if now is None:
        now = datetime.now()
    
    try:
        ts = datetime.fromisoformat(timestamp_str)
    except (ValueError, TypeError):
        return 1.0
    
    days_delayed = (now - ts).days
    multiplier = 1.0 + (0.1 * days_delayed)
    
    return max(1.0, multiplier)  # حداقل 1.0


def compute_priority_score(safety: int, class_disruption: int, infrastructure: int, 
                          weights: dict, waiting_multiplier: float = 1.0) -> float:
    """
    محاسبه Priority Score نهایی
    
    فرمول:
    Priority = (w_s * Safety + w_cd * Class_Disruption + w_ic * Infrastructure) × waiting_multiplier
    
    Parameters
    ----------
    safety : int (1-9)
        امتیاز معیار ایمنی
    class_disruption : int (1-9)
        امتیاز معیار اختلال در کلاس
    infrastructure : int (1-10)
        امتیاز معیار بحرانی‌بودن خدمت
    weights : dict
        خروجی ahp.compute_ahp_weights()["weights"]
        شامل keys: "Safety", "Class_Disruption", "Infrastructure_Criticality"
    waiting_multiplier : float
        ضریب زمانی (پیش‌فرض: 1.0 = بدون تاخیر)
    
    Returns
    -------
    float
        Priority Score نهایی
    """
    base_score = (
        weights["Safety"] * safety +
        weights["Class_Disruption"] * class_disruption +
        weights["Infrastructure_Criticality"] * infrastructure
    )
    
    final_score = base_score * waiting_multiplier
    return final_score


def priority_level(score: float) -> tuple:
    """
    تبدیل Priority Score به سطح اولویت
    
    Returns
    -------
    tuple: (level_name, emoji)
    """
    if score >= 7:
        return "بحرانی", "🔴"
    elif score >= 5:
        return "بالا", "🟠"
    elif score >= 3:
        return "متوسط", "🟡"
    else:
        return "پایین", "🟢"


if __name__ == "__main__":
    # تست
    from ahp_updated import compute_ahp_weights
    
    weights = compute_ahp_weights()["weights"]
    print("وزن‌ها:", weights)
    
    # تست: Safety=9, Class_Disruption=5, Infrastructure=8, بدون تاخیر
    score_no_wait = compute_priority_score(9, 5, 8, weights, 1.0)
    print(f"\nتست 1 (بدون تاخیر): {score_no_wait:.2f} - {priority_level(score_no_wait)}")
    
    # تست: همان، اما با 5 روز تاخیر
    multiplier_5days = 1.0 + (0.1 * 5)
    score_5days = compute_priority_score(9, 5, 8, weights, multiplier_5days)
    print(f"تست 2 (5 روز تاخیر، ضریب={multiplier_5days}): {score_5days:.2f} - {priority_level(score_5days)}")
    
    # تست: Safety=3, Class_Disruption=1, Infrastructure=1
    score_low = compute_priority_score(3, 1, 1, weights, 1.0)
    print(f"تست 3 (کم‌اهمیت): {score_low:.2f} - {priority_level(score_low)}")
