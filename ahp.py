# -*- coding: utf-8 -*-
"""
ماژول محاسبات AHP (Analytic Hierarchy Process)
شامل: محاسبه وزن معیارها با روش مجموع نرمال‌شده ستون‌ها (NCS)،
محاسبه لاندا-ماکس، شاخص سازگاری (CI) و نرخ سازگاری (CR).
"""

import numpy as np

# شاخص تصادفی (Random Index) ساعتی - جدول استاندارد Saaty
RI_TABLE = {1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45}

# ترتیب معیارها دقیقاً مطابق مشخصات Demo
CRITERIA_NAMES = ["Safety", "Affected_People", "Class_Disruption", "Waiting_Time"]

# ماتریس مقایسه زوجی پیش‌فرض Demo (وزن‌ها فرضی هستند و بعداً با نظر خبره جایگزین می‌شوند)
PAIRWISE_MATRIX = [
    [1,     3,     3,     5],
    [1 / 3, 1,     1,     3],
    [1 / 3, 1,     1,     3],
    [1 / 5, 1 / 3, 1 / 3, 1],
]


def compute_ahp_weights(matrix=None, criteria_names=None):
    """
    محاسبه وزن معیارها با روش مجموع نرمال‌شده ستون‌ها (Normalized Column Sum)
    و اعتبارسنجی سازگاری قضاوت‌ها با محاسبه Consistency Ratio.

    Parameters
    ----------
    matrix : list[list[float]] یا None
        ماتریس مقایسه زوجی n×n. اگر None باشد، از PAIRWISE_MATRIX پیش‌فرض استفاده می‌شود.
    criteria_names : list[str] یا None
        نام معیارها به همان ترتیب سطرها/ستون‌های ماتریس.

    Returns
    -------
    dict شامل:
        weights: dict {نام معیار: وزن}
        lambda_max: بزرگ‌ترین مقدار ویژه ماتریس
        CI: شاخص سازگاری
        CR: نرخ سازگاری
        is_consistent: True اگر CR < 0.1
    """
    if matrix is None:
        matrix = PAIRWISE_MATRIX
    if criteria_names is None:
        criteria_names = CRITERIA_NAMES

    A = np.array(matrix, dtype=float)
    n = A.shape[0]

    if A.shape[0] != A.shape[1]:
        raise ValueError("ماتریس مقایسه زوجی باید مربعی باشد.")
    if len(criteria_names) != n:
        raise ValueError("تعداد نام معیارها باید با ابعاد ماتریس برابر باشد.")

    # مرحله ۱ و ۲: نرمال‌سازی هر ستون بر مجموع همان ستون
    col_sums = A.sum(axis=0)
    normalized = A / col_sums

    # مرحله ۳: میانگین هر سطر = وزن همان معیار
    weights = normalized.mean(axis=1)

    # محاسبه Aw و لاندا-ماکس برای آزمون سازگاری
    Aw = A @ weights
    lambdas = Aw / weights
    lambda_max = float(lambdas.mean())

    CI = (lambda_max - n) / (n - 1) if n > 1 else 0.0
    RI = RI_TABLE.get(n, 1.49)
    CR = (CI / RI) if RI != 0 else 0.0

    return {
        "weights": dict(zip(criteria_names, weights.tolist())),
        "lambda_max": lambda_max,
        "CI": CI,
        "CR": CR,
        "is_consistent": CR < 0.1,
    }


if __name__ == "__main__":
    # اجرای مستقل برای تست سریع محاسبات
    result = compute_ahp_weights()
    print("وزن معیارها:")
    for name, w in result["weights"].items():
        print(f"  {name}: {w:.3f}")
    print(f"Lambda max: {result['lambda_max']:.4f}")
    print(f"CI: {result['CI']:.4f}")
    print(f"CR: {result['CR']:.4f}")
    print(f"سازگار: {result['is_consistent']}")
