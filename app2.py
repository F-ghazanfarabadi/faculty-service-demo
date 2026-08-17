# -*- coding: utf-8 -*-
"""
سامانه هوشمند مدیریت و تخصیص شکایات دانشکده — Demo
====================================================
معماری سه‌نقشی روی یک اپ واحد (بدون نیاز به سه دیپلوی جدا):

    لینک دانشجو (ثبت شکایت):   .../?location=A11
    لینک کارکنان:              .../?role=staff
    لینک مدیر پروژه (داشبورد):  .../?role=admin

هر نقش فقط صفحه‌ی مخصوص خودش را می‌بیند؛ نه نوار کناری مشترک وجود دارد و
نه امکان پرش بین نقش‌ها از داخل اپ. دانشجوی ثبت‌کننده‌ی شکایت هیچ‌گاه
جزئیات مدل AHP/PuLP، هویت کارکنان یا پنل آن‌ها را نمی‌بیند.
"""

import os
import time
from datetime import datetime

import pandas as pd
import streamlit as st

from ahp import compute_ahp_weights
from scoring import (
    SAFETY_OPTIONS,
    AFFECTED_PEOPLE_OPTIONS,
    CLASS_DISRUPTION_OPTIONS,
    CATEGORY_OPTIONS,
    waiting_time_score,
    compute_priority,
    priority_level,
)
from optimization import assign_complaints

# ============================================================
# تنظیمات پایه
# ============================================================
DATA_DIR = "data"
COMPLAINTS_FILE = os.path.join(DATA_DIR, "complaints.csv")
WORKERS_FILE = os.path.join(DATA_DIR, "workers.csv")

# کد دسترسی مدیر — این فقط یک قفل نمادین برای Demo است، نه احراز هویت واقعی.
# در نسخه اصلی باید با لاگین واقعی (نام کاربری/رمز یا SSO دانشگاه) جایگزین شود.
ADMIN_PIN = "1234"

COMPLAINT_COLUMNS = [
    "id", "location", "description", "category", "safety", "affected_people",
    "class_disruption", "waiting_time", "priority", "priority_level",
    "status", "assigned_worker", "timestamp",
]

st.set_page_config(
    page_title="سامانه خدمات دانشکده",
    page_icon="🏫",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;600;700&display=swap');
    html, body, [class*="css"]  { font-family: 'Vazirmatn', sans-serif; }
    .main .block-container { direction: rtl; text-align: right; }
    div[data-testid="stForm"] { direction: rtl; text-align: right; }
    .stRadio > label, .stSelectbox > label, .stTextArea > label { direction: rtl; text-align: right; }
    div[role="radiogroup"] { direction: rtl; }
    .location-badge {
        background: #EAF1F8; border: 1px solid #1C7293; color: #1E2761;
        padding: 8px 16px; border-radius: 8px; display: inline-block;
        font-weight: 600; margin-bottom: 12px;
    }
    .result-card {
        background: #F2F6F9; border-radius: 12px; padding: 20px; margin-top: 12px;
        border-right: 5px solid #1C7293;
    }
    .role-tag {
        background: #1E2761; color: white; padding: 4px 12px; border-radius: 999px;
        font-size: 12px; display: inline-block; margin-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# توابع کمکی ذخیره/بازیابی داده (مشترک بین هر سه نقش)
# ============================================================

def load_complaints() -> pd.DataFrame:
    if os.path.exists(COMPLAINTS_FILE):
        df = pd.read_csv(COMPLAINTS_FILE, dtype=str)
        if df.empty:
            return pd.DataFrame(columns=COMPLAINT_COLUMNS)
        for col in ["safety", "affected_people", "class_disruption", "waiting_time", "priority"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df
    return pd.DataFrame(columns=COMPLAINT_COLUMNS)


def save_complaints(df: pd.DataFrame):
    df.to_csv(COMPLAINTS_FILE, index=False)


def load_workers() -> pd.DataFrame:
    df = pd.read_csv(WORKERS_FILE, dtype=str)
    df["distance"] = pd.to_numeric(df["distance"], errors="coerce")
    return df


def save_workers(df: pd.DataFrame):
    df.to_csv(WORKERS_FILE, index=False)


def next_complaint_id(df: pd.DataFrame) -> str:
    if df.empty:
        return "C001"
    nums = df["id"].str.replace("C", "", regex=False).astype(int)
    return f"C{nums.max() + 1:03d}"


def try_assign_pending():
    """تلاش مجدد برای تخصیص شکایاتی که هنوز نیرو نگرفته‌اند (پس از آزاد شدن یک کارمند)."""
    complaints_df = load_complaints()
    workers_df = load_workers()

    pending = complaints_df[complaints_df["status"].isin(["Waiting", "Waiting for Worker"])]
    if pending.empty:
        return

    complaints_list = [{"id": r["id"], "category": r["category"]} for _, r in pending.iterrows()]
    workers_list = workers_df.to_dict("records")
    result = assign_complaints(complaints_list, workers_list)

    for cid, wid in result["assignments"].items():
        complaints_df.loc[complaints_df["id"] == cid, "status"] = "Assigned"
        complaints_df.loc[complaints_df["id"] == cid, "assigned_worker"] = wid
        workers_df.loc[workers_df["worker_id"] == wid, "available"] = "مشغول"

    if result["assignments"]:
        save_complaints(complaints_df)
        save_workers(workers_df)


# ============================================================
# نقش ۱: دانشجو / ثبت‌کننده شکایت   →   ?location=A11
# فقط فرم ثبت و یک پیام نتیجه ساده؛ هیچ جزئیات مدل یا هویت کارکنان نمایش داده نمی‌شود.
# ============================================================

def render_citizen_page():
    location = st.query_params.get("location", "A11")

    st.markdown(f'<div class="location-badge">📍 مکان گزارش: کلاس {location}</div>', unsafe_allow_html=True)
    st.title("سامانه مدیریت خدمات دانشکده")
    st.caption(f"ثبت مشکل در کلاس {location}")

    with st.form("complaint_form", clear_on_submit=False):
        description = st.text_area(
            "مشکل خود را توضیح دهید.",
            placeholder="مثلاً: کولر کلاس خراب است و دمای کلاس بسیار بالاست.",
        )
        category = st.selectbox("نوع مشکل", CATEGORY_OPTIONS)

        st.markdown("**این مشکل چه میزان تأثیری بر ایمنی افراد دارد؟**")
        safety_label = st.radio("safety", list(SAFETY_OPTIONS.keys()), label_visibility="collapsed")

        st.markdown("**چند نفر تحت تأثیر این مشکل قرار گرفته‌اند؟**")
        affected_label = st.radio("affected", list(AFFECTED_PEOPLE_OPTIONS.keys()), label_visibility="collapsed")

        st.markdown("**آیا این مشکل در برگزاری کلاس اختلال ایجاد کرده است؟**")
        disruption_label = st.radio("disruption", list(CLASS_DISRUPTION_OPTIONS.keys()), label_visibility="collapsed")

        submitted = st.form_submit_button("ثبت شکایت", use_container_width=True)

    if not submitted:
        return

    if not description or not description.strip():
        st.error("لطفاً توضیح مشکل را وارد کنید.")
        st.stop()

    complaints_df = load_complaints()
    cid = next_complaint_id(complaints_df)
    timestamp = datetime.now().isoformat()

    safety = SAFETY_OPTIONS[safety_label]
    affected = AFFECTED_PEOPLE_OPTIONS[affected_label]
    disruption = CLASS_DISRUPTION_OPTIONS[disruption_label]
    waiting = waiting_time_score(timestamp)

    # --- محاسبات AHP/اولویت در پس‌زمینه انجام می‌شود؛ به کاربر نمایش داده نمی‌شود ---
    weights = compute_ahp_weights()["weights"]
    priority = compute_priority(safety, affected, disruption, waiting, weights)
    level, emoji = priority_level(priority)

    new_row = {
        "id": cid, "location": location, "description": description.strip(),
        "category": category, "safety": safety, "affected_people": affected,
        "class_disruption": disruption, "waiting_time": waiting,
        "priority": round(priority, 2), "priority_level": level,
        "status": "Waiting", "assigned_worker": "", "timestamp": timestamp,
    }
    complaints_df = pd.concat([complaints_df, pd.DataFrame([new_row])], ignore_index=True)
    save_complaints(complaints_df)

    with st.spinner("در حال ثبت و ارجاع درخواست..."):
        time.sleep(0.6)
        workers_df = load_workers()
        result = assign_complaints([{"id": cid, "category": category}], workers_df.to_dict("records"))

        if result["status"] == "assigned" and cid in result["assignments"]:
            wid = result["assignments"][cid]
            complaints_df.loc[complaints_df["id"] == cid, "status"] = "Assigned"
            complaints_df.loc[complaints_df["id"] == cid, "assigned_worker"] = wid
            workers_df.loc[workers_df["worker_id"] == wid, "available"] = "مشغول"
            save_complaints(complaints_df)
            save_workers(workers_df)
            final_status_text = "در حال رسیدگی — نیروی مربوطه اطلاع‌رسانی شد"
        else:
            complaints_df.loc[complaints_df["id"] == cid, "status"] = "Waiting for Worker"
            save_complaints(complaints_df)
            final_status_text = "در صف انتظار — به‌محض آزاد شدن نیرو رسیدگی می‌شود"

    # --- نمایش نتیجه: فقط اطلاعاتی که برای خودِ کاربر مربوط است، بدون هیچ جزئیات مدل یا هویت کارمند ---
    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    st.success("✅ شکایت شما با موفقیت ثبت شد.")
    st.write(f"**شماره پیگیری:** {cid}")
    st.write(f"**مکان:** کلاس {location}")
    st.write(f"**اولویت:** {emoji} {level}")
    st.write(f"**وضعیت:** {final_status_text}")
    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# نقش ۲: کارکنان خدمات   →   ?role=staff
# فقط فهرست مأموریت‌های خودشان؛ بدون وزن‌های AHP، بدون فهرست کل شکایات دانشکده.
# ============================================================

def render_staff_page():
    st.markdown('<span class="role-tag">👷 پنل کارکنان</span>', unsafe_allow_html=True)
    st.title("پنل کارکنان خدمات")

    workers_df = load_workers()
    worker_options = {
        f"{row.worker_id} — {row.name} ({row.skill})": row.worker_id
        for row in workers_df.itertuples()
    }
    selected_label = st.selectbox("کارمند خود را انتخاب کنید", list(worker_options.keys()))
    selected_wid = worker_options[selected_label]

    if st.button("🔄 به‌روزرسانی"):
        st.rerun()

    complaints_df = load_complaints()
    my_tasks = complaints_df[
        (complaints_df["assigned_worker"] == selected_wid)
        & (complaints_df["status"].isin(["Assigned", "In Progress"]))
    ]

    if my_tasks.empty:
        st.info("در حال حاضر مأموریت جدیدی برای شما ثبت نشده است.")
    else:
        for _, task in my_tasks.iterrows():
            with st.container(border=True):
                st.markdown("### 🔔 درخواست جدید" if task["status"] == "Assigned" else "### 🔧 در حال انجام")
                st.write(f"**شناسه:** {task['id']}")
                st.write(f"**مکان:** کلاس {task['location']}")
                st.write(f"**دسته‌بندی:** {task['category']}")
                st.write(f"**اولویت:** {task['priority_level']}")
                st.write(f"**شرح:** {task['description']}")

                col1, col2 = st.columns(2)
                if task["status"] == "Assigned":
                    if col1.button("✅ پذیرش کار", key=f"accept_{task['id']}"):
                        complaints_df.loc[complaints_df["id"] == task["id"], "status"] = "In Progress"
                        save_complaints(complaints_df)
                        st.rerun()
                elif task["status"] == "In Progress":
                    if col1.button("🏁 تکمیل کار", key=f"complete_{task['id']}"):
                        complaints_df.loc[complaints_df["id"] == task["id"], "status"] = "Completed"
                        save_complaints(complaints_df)
                        workers_df.loc[workers_df["worker_id"] == selected_wid, "available"] = "آزاد"
                        save_workers(workers_df)
                        try_assign_pending()
                        st.rerun()

    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=8000, key="staff_panel_refresh")
    except ImportError:
        st.caption("برای به‌روزرسانی خودکار، کتابخانه streamlit-autorefresh را نصب کنید (اختیاری).")


# ============================================================
# نقش ۳: مدیر پروژه / داشبورد   →   ?role=admin
# تمام جزئیات مدل AHP، مدل PuLP، فهرست کامل شکایات و کارکنان.
# پشت یک کد دسترسی نمادین قرار دارد (فقط برای Demo، نه امنیت واقعی).
# ============================================================

def render_admin_page():
    st.markdown('<span class="role-tag">🛠️ داشبورد مدیریت پروژه</span>', unsafe_allow_html=True)
    st.title("داشبورد مدیریتی")

    pin = st.text_input("کد دسترسی مدیر", type="password")
    if pin != ADMIN_PIN:
        st.warning("این صفحه فقط برای مدیر پروژه است. کد دسترسی را وارد کنید.")
        st.caption("(این یک قفل نمادین برای Demo است؛ در نسخه اصلی باید با احراز هویت واقعی جایگزین شود.)")
        st.stop()

    st.success("✅ دسترسی مدیر تأیید شد.")

    # ---- لینک‌های سه‌گانه برای استفاده در ارائه ----
    with st.expander("🔗 لینک‌های هر نقش (برای دمو)", expanded=False):
        st.code("لینک دانشجو:   <آدرس‌اپ>/?location=A11\nلینک کارکنان:   <آدرس‌اپ>/?role=staff\nلینک مدیر:      <آدرس‌اپ>/?role=admin")

    st.markdown("---")
    st.subheader("📐 مدل AHP — وزن معیارها")
    ahp_result = compute_ahp_weights()
    w_cols = st.columns(4)
    for i, (name, w) in enumerate(ahp_result["weights"].items()):
        w_cols[i].metric(name, f"{w:.3f}")
    c1, c2, c3 = st.columns(3)
    c1.metric("λmax", f"{ahp_result['lambda_max']:.4f}")
    c2.metric("CI", f"{ahp_result['CI']:.4f}")
    c3.metric("CR", f"{ahp_result['CR']:.4f}")
    if ahp_result["is_consistent"]:
        st.success("✅ ماتریس مقایسه زوجی سازگار است (CR < 0.1).")
    else:
        st.error("❌ ماتریس ناسازگار است؛ باید مصاحبه خبرگان تکرار شود.")

    with st.expander("مشاهده ماتریس مقایسه زوجی"):
        from ahp import PAIRWISE_MATRIX, CRITERIA_NAMES
        st.dataframe(pd.DataFrame(PAIRWISE_MATRIX, index=CRITERIA_NAMES, columns=CRITERIA_NAMES).round(3),
                     use_container_width=True)

    st.markdown("---")
    st.subheader("⚙️ مدل تخصیص (PuLP)")
    st.latex(r"\min Z = \sum_i \sum_j d_{ij} x_{ij}")
    st.caption("محدودیت‌ها: هر شکایت واجدشرایط دقیقاً به یک کارمند تخصیص یابد؛ هر کارمند حداکثر یک کار؛ فقط زوج‌های هم‌تخصص و آزاد وارد مدل می‌شوند.")

    st.markdown("---")
    st.subheader("📋 فهرست کامل شکایات")
    complaints_df = load_complaints()
    if complaints_df.empty:
        st.info("هنوز شکایتی ثبت نشده است.")
    else:
        st.dataframe(
            complaints_df.sort_values("priority", ascending=False)[
                ["id", "location", "category", "priority", "priority_level", "status", "assigned_worker", "timestamp"]
            ],
            use_container_width=True, hide_index=True,
        )

    st.markdown("---")
    st.subheader("👷 وضعیت کارکنان")
    workers_df = load_workers()
    st.dataframe(workers_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    with st.expander("🔗 تولید QR Code برای یک مکان"):
        base_url = st.text_input("آدرس دمو (بعد از دیپلوی روی Streamlit Cloud اینجا بگذارید)", "https://your-app.streamlit.app")
        loc_for_qr = st.text_input("شناسه مکان", "A11")
        if st.button("تولید QR"):
            try:
                import qrcode
                from io import BytesIO
                qr_img = qrcode.make(f"{base_url}?location={loc_for_qr}")
                buf = BytesIO()
                qr_img.save(buf, format="PNG")
                st.image(buf.getvalue(), width=220)
            except ImportError:
                st.error("کتابخانه qrcode نصب نیست: pip install qrcode[pil]")


# ============================================================
# مسیریابی بر اساس نقش (خواندن از query param — هیچ نوار کناری مشترکی وجود ندارد)
# ============================================================

role = st.query_params.get("role", "citizen")

if role == "staff":
    render_staff_page()
elif role == "admin":
    render_admin_page()
else:
    render_citizen_page()
