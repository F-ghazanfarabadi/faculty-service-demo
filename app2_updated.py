#-*- coding: utf-8 -*-
"""
سامانه هوشمند مدیریت شکایات دانشکده — Demo

فرم جدید برای دانشجویان:
1. مکان شکایت
2. ایمنی (Safety)
3. اختلال در کلاس (Class_Disruption)
4. بحرانی‌بودن خدمت (Infrastructure_Criticality)
5. دسته‌بندی خدمات

سپس نمایش Score با ضریب زمانی
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime
from ahp_updated import compute_ahp_weights
from scoring_updated import (
    SAFETY_OPTIONS, 
    CLASS_DISRUPTION_OPTIONS,
    INFRASTRUCTURE_OPTIONS,
    CATEGORY_OPTIONS,
    compute_priority_score,
    compute_waiting_time_multiplier,
    priority_level
)

st.set_page_config(page_title="سامانه شکایات", layout="wide")

# Title
st.title("🏫 سامانه هوشمند مدیریت شکایات دانشکده")

# Initialize session state
if "complaints_data" not in st.session_state:
    st.session_state.complaints_data = []

# Calculate AHP weights
ahp_result = compute_ahp_weights()
weights = ahp_result["weights"]

st.markdown("---")
st.header("📝 ثبت شکایت جدید")

# فرم ثبت شکایت
with st.form("complaint_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        location = st.text_input(
            "📍 مکان شکایت (مثل: اتاق A11، آزمایشگاه B3):",
            value="A11",
            help="مشخص کنید شکایت از کجا گزارش شده"
        )
    
    with col2:
        category = st.selectbox(
            "🔧 دسته‌بندی خدمات:",
            CATEGORY_OPTIONS,
            help="کدام بخش را نیاز است؟"
        )
    
    # معیار ۱: ایمنی
    st.subheader("1️⃣ معیار ایمنی")
    safety_answer = st.radio(
        "تأثیر بر ایمنی:",
        list(SAFETY_OPTIONS.keys()),
        help="میزان خطر ایمنی شکایت را انتخاب کنید"
    )
    safety_score = SAFETY_OPTIONS[safety_answer]
    st.caption(f"✓ امتیاز: {safety_score}")
    
    # معیار ۲: اختلال در کلاس
    st.subheader("2️⃣ معیار اختلال در کلاس")
    disruption_answer = st.radio(
        "تأثیر بر برگزاری کلاس:",
        list(CLASS_DISRUPTION_OPTIONS.keys()),
        help="آیا این شکایت کلاس را مختل می‌کند؟"
    )
    disruption_score = CLASS_DISRUPTION_OPTIONS[disruption_answer]
    st.caption(f"✓ امتیاز: {disruption_score}")
    
    # معیار ۳: بحرانی‌بودن خدمت
    st.subheader("3️⃣ معیار بحرانی‌بودن خدمت")
    infrastructure_answer = st.radio(
        "بحرانی‌بودن خدمت (اسیب به زیرساخت و داراییه):",
        list(INFRASTRUCTURE_OPTIONS.keys()),
        help="این شکایت چقدر بر زیرساخت دانشکده تأثیر میگذارد؟"
    )
    infrastructure_score = INFRASTRUCTURE_OPTIONS[infrastructure_answer]
    st.caption(f"✓ امتیاز: {infrastructure_score}")
    
    # دکمهٔ ثبت
    submitted = st.form_submit_button("✅ ثبت شکایت", use_container_width=True)

if submitted:
    timestamp = datetime.now().isoformat()
    complaint_id = f"C{len(st.session_state.complaints_data) + 1:03d}"
    
    # محاسبه ضریب زمانی (در اینجا 0 روز = 1.0)
    waiting_multiplier = compute_waiting_time_multiplier(timestamp)
    
    # محاسبه Priority Score
    priority_score = compute_priority_score(
        safety_score, 
        disruption_score, 
        infrastructure_score,
        weights,
        waiting_multiplier
    )
    
    level_name, emoji = priority_level(priority_score)
    
    # ذخیره اطلاعات
    complaint_data = {
        "id": complaint_id,
        "timestamp": timestamp,
        "location": location,
        "category": category,
        "safety_score": safety_score,
        "disruption_score": disruption_score,
        "infrastructure_score": infrastructure_score,
        "waiting_multiplier": waiting_multiplier,
        "priority_score": priority_score,
        "priority_level": level_name,
        "status": "ثبت‌شده"
    }
    
    st.session_state.complaints_data.append(complaint_data)
    
    # نمایش نتیجه
    st.success("✅ شکایت با موفقیت ثبت شد!")
    
    with st.container():
        st.markdown("---")
        st.subheader(f"{emoji} نتیجهٔ تحلیل")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("شناسهٔ شکایت", complaint_id)
        with col2:
            st.metric("اولویت", f"{priority_score:.2f}")
        with col3:
            st.metric("سطح", level_name)
        with col4:
            st.metric("ضریب زمانی", f"{waiting_multiplier:.1f}×")
        
        # جزئیات امتیازات
        st.markdown("**تفکیک امتیازات:**")
        score_df = pd.DataFrame([
            {"معیار": "ایمنی", "امتیاز": safety_score, "وزن": f"{weights['Safety']:.3f}"},
            {"معیار": "اختلال کلاس", "امتیاز": disruption_score, "وزن": f"{weights['Class_Disruption']:.3f}"},
            {"معیار": "بحرانی‌بودن", "امتیاز": infrastructure_score, "وزن": f"{weights['Infrastructure_Criticality']:.3f}"},
        ])
        st.dataframe(score_df, use_container_width=True, hide_index=True)
        
        st.info(f"""
        📊 **محاسبه:**
        - Base Score = {weights['Safety']:.3f}×{safety_score} + {weights['Class_Disruption']:.3f}×{disruption_score} + {weights['Infrastructure_Criticality']:.3f}×{infrastructure_score}
        - Base Score ≈ {priority_score / waiting_multiplier:.2f}
        - Final Score = {priority_score / waiting_multiplier:.2f} × {waiting_multiplier:.1f} = **{priority_score:.2f}**
        """)

# نمایش داشبورد شکایات
if st.session_state.complaints_data:
    st.markdown("---")
    st.header("📊 داشبورد شکایات")
    
    df = pd.DataFrame(st.session_state.complaints_data)
    
    # آمار کلی
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("تعداد شکایات", len(df))
    with col2:
        avg_score = df["priority_score"].mean()
        st.metric("میانگین اولویت", f"{avg_score:.2f}")
    with col3:
        critical_count = len(df[df["priority_level"] == "بحرانی"])
        st.metric("شکایات بحرانی", critical_count)
    with col4:
        low_count = len(df[df["priority_level"] == "پایین"])
        st.metric("شکایات پایین", low_count)
    
    # جدول شکایات
    st.subheader("📋 لیست شکایات")
    display_df = df[["id", "location", "category", "priority_level", "priority_score", "status"]].copy()
    display_df.columns = ["شناسه", "مکان", "دسته", "اولویت", "امتیاز", "وضعیت"]
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # نمودار توزیع اولویت‌ها
    st.subheader("📈 توزیع اولویت‌ها")
    priority_counts = df["priority_level"].value_counts()
    st.bar_chart(priority_counts)

# اطلاعات AHP
with st.expander("ℹ️ اطلاعات AHP و وزن‌ها"):
    st.write("**وزن‌های معیارها:**")
    weights_df = pd.DataFrame([
        {"معیار": k, "وزن": f"{v:.4f}"} 
        for k, v in weights.items()
    ])
    st.dataframe(weights_df, use_container_width=True, hide_index=True)
    
    st.write(f"**نسبت‌های تائید:**")
    w = weights
    ratios = f"""
    - Safety : Class_Disruption = {w['Safety']/w['Class_Disruption']:.2f}:1 ✓
    - Safety : Infrastructure = {w['Safety']/w['Infrastructure_Criticality']:.2f}:1 ✓
    - Class_Disruption : Infrastructure = {w['Class_Disruption']/w['Infrastructure_Criticality']:.2f}:1 ✓
    
    **سازگاری:** CR = {ahp_result['CR']:.4f} {'✓ (سازگار)' if ahp_result['is_consistent'] else '❌ (نامناسب)'}
    """
    st.info(ratios)
