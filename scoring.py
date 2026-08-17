# -*- coding: utf-8 -*-
"""
ماژول امتیازدهی: تبدیل پاسخ‌های کاربر (گزینه‌های متنی) به امتیازهای عددی معیارها،
محاسبه امتیاز معیار زمان انتظار بر اساس زمان سپری‌شده، و تعیین سطح اولویت نهایی.
"""

from datetime import datetime

# ---- معیار ۱: تأثیر بر ایمنی ----
SAFETY_OPTIONS = {
    "هیچ تأثیری بر ایمنی ندارد": 1,
    "ممکن است در آینده باعث مشکل ایمنی شود": 5,
    "در حال حاضر خطر ایمنی ایجاد می‌کند": 7,
    "خطر ایمنی جدی و فوری ایجاد می‌کند": 9,
}

# ---- معیار ۲: تعداد افراد متأثر ----
AFFECTED_PEOPLE_OPTIONS = {
    "1 تا 5 نفر": 1,
    "6 تا 10 نفر": 3,
    "11 تا 15 نفر": 5,
    "16 تا 25 نفر": 7,
    "26 تا 30 نفر": 9,
}

# ---- معیار ۳: اختلال در برگزاری کلاس ----
CLASS_DISRUPTION_OPTIONS = {
    "خیر، هیچ اختلالی ایجاد نکرده": 1,
    "اختلال جزئی ایجاد کرده": 3,
    "اختلال قابل توجه ایجاد کرده": 5,
    "برگزاری کلاس را مختل یا متوقف کرده": 9,
}

# دسته‌بندی مشکل — این فیلد در مشخصات اصلی برای فرم ذکر نشده بود اما برای مرحله
# تخصیص (تطبیق تخصص کارمند با نوع مشکل) ضروری است؛ گزینه‌ها منطبق با ستون skill
# در workers.csv انتخاب شده‌اند.
CATEGORY_OPTIONS = ["برق", "تأسیسات", "نظافت", "عمومی"]


def waiting_time_score(timestamp_str: str, now: datetime = None) -> int:
    """
    امتیاز معیار زمان انتظار بر اساس فاصله زمانی بین لحظه ثبت شکایت و اکنون.
    این مقیاس فرضی است و صرفاً برای Demo استفاده می‌شود؛ در نسخه پژوهشی نهایی
    باید با منبع علمی یا نظر خبره اعتبارسنجی شود.
    """
    if now is None:
        now = datetime.now()
    ts = datetime.fromisoformat(timestamp_str)
    hours = (now - ts).total_seconds() / 3600

    if hours < 1:
        return 1
    elif hours < 4:
        return 3
    elif hours < 8:
        return 5
    elif hours < 24:
        return 7
    else:
        return 9


def compute_priority(safety, affected_people, class_disruption, waiting_time, weights):
    """
    محاسبه Priority Score نهایی از ترکیب وزنی چهار معیار.
    weights: دیکشنری خروجی ahp.compute_ahp_weights()["weights"]
    """
    return (
        weights["Safety"] * safety
        + weights["Affected_People"] * affected_people
        + weights["Class_Disruption"] * class_disruption
        + weights["Waiting_Time"] * waiting_time
    )


def priority_level(score: float):
    """
    تبدیل Priority Score به سطح اولویت قابل نمایش (برچسب + ایموجی).
    آستانه‌ها فرضی و مخصوص Demo هستند.
    """
    if score >= 7:
        return "بحرانی", "🔴"
    elif score >= 5:
        return "بالا", "🟠"
    elif score >= 3:
        return "متوسط", "🟡"
    else:
        return "پایین", "🟢"
