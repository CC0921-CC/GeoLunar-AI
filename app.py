
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# 找到真实科研数据
DATA_FILE = (
    Path(__file__).parent
    / "data"
    / "raw"
    / "CE6_LMS_Supplementary_DataS2.xlsx"
)

st.set_page_config(page_title="GeoLunar AI", layout="wide")

st.title("🌕 GeoLunar AI")
st.subheader("嫦娥六号真实光谱分析实验室")

if not DATA_FILE.exists():
    st.error(f"找不到数据文件：{DATA_FILE}")
    st.stop()

# 读取 Excel
excel = pd.ExcelFile(DATA_FILE)

sheet = st.selectbox(
    "选择观测样本",
    excel.sheet_names
)

df = pd.read_excel(
    DATA_FILE,
    sheet_name=sheet,
    header=1
)

# 每组数据使用各自对应的波长列和数据列
options = {
    "连续反射率": (10, 11),
    "含缺口反射率": (2, 8),
    "单次散射反照率": (20, 21),
    "平滑反射率（SSA）": (20, 22),
    "相对反射率（SSA）": (24, 27),
}

choice = st.selectbox(
    "选择分析数据",
    list(options.keys())
)

x_col, y_col = options[choice]

# 提取对应波长和观测值
wavelength = pd.to_numeric(
    df.iloc[:, x_col],
    errors="coerce"
)

signal = pd.to_numeric(
    df.iloc[:, y_col],
    errors="coerce"
)

data = pd.DataFrame({
    "Wavelength (nm)": wavelength,
    "Signal": signal
}).dropna()

data = data.sort_values("Wavelength (nm)")

# 绘制光谱
fig, ax = plt.subplots(figsize=(11, 5))

ax.plot(
    data["Wavelength (nm)"],
    data["Signal"],
    linewidth=1.5
)

ax.set_xlabel("Wavelength (nm)")
ax.set_ylabel(choice)
ax.set_title(f"{sheet} - {choice}")
ax.grid(alpha=0.3)

st.pyplot(fig)
# 关键波段分析
st.subheader("🔬 OH/H₂O 关键波段观察")

region = data[
    (data["Wavelength (nm)"] >= 2700) &
    (data["Wavelength (nm)"] <= 3100)
]

if len(region) > 0:
    fig2, ax2 = plt.subplots(figsize=(10, 4))

    ax2.plot(
        region["Wavelength (nm)"],
        region["Signal"],
        marker=".",
        linewidth=1.5
    )

    ax2.axvline(
        2850,
        linestyle="--",
        label="2850 nm"
    )

    ax2.set_xlabel("Wavelength (nm)")
    ax2.set_ylabel(choice)
    ax2.set_title("2700–3100 nm Spectral Detail")
    ax2.legend()
    ax2.grid(alpha=0.3)

    st.pyplot(fig2)
else:
    st.warning("当前数据没有有效的 2700–3100 nm 波段。")

# 展示数据
st.subheader("光谱数据预览")
st.dataframe(data, use_container_width=True)

st.success(f"成功读取 {len(data)} 个有效数据点！")
# 关键波段局部分析
st.subheader("🔬 OH/H2O 关键波段分析")

region = data[
    (data["Wavelength (nm)"] >= 2700) &
    (data["Wavelength (nm)"] <= 3100)
]

if len(region) > 0:
    fig2, ax2 = plt.subplots(figsize=(10, 4))

    ax2.plot(
        region["Wavelength (nm)"],
        region["Signal"]
    )

    ax2.axvline(
        2850,
        linestyle="--",
        label="2850 nm"
    )

    ax2.set_xlabel("Wavelength (nm)")
    ax2.set_ylabel(choice)
    ax2.set_title("Lunar Spectral Detail")
    ax2.legend()
    ax2.grid(alpha=0.3)

    st.pyplot(fig2)
else:
    st.warning("该波段没有有效数据")
# 自动识别局部吸收谷
st.subheader("🔍 自动吸收特征识别")

import numpy as np

if len(data) >= 3:

    values = data["Signal"].to_numpy()
    wavelengths = data["Wavelength (nm)"].to_numpy()

    valleys = []

    for i in range(1, len(values) - 1):

        if values[i] < values[i-1] and values[i] < values[i+1]:

            valleys.append({
                "波长 (nm)": round(wavelengths[i], 2),
                "信号值": round(values[i], 5)
            })

    if valleys:
        st.write("发现以下局部低谷：")
        st.dataframe(valleys, use_container_width=True)
    else:
        st.info("暂未发现局部低谷。")

# 定量分析吸收特征
st.subheader("📊 光谱吸收定量分析")

band = data[
    (data["Wavelength (nm)"] >= 2700) &
    (data["Wavelength (nm)"] <= 3100)
].copy()

if len(band) >= 3:

    x = band["Wavelength (nm)"].to_numpy()
    y = band["Signal"].to_numpy()

    # 建立简单的线性连续谱基线
    continuum = np.linspace(y[0], y[-1], len(y))

    # 计算连续谱去除后的相对吸收深度
    valid = continuum > 0

    x = x[valid]
    y = y[valid]
    continuum = continuum[valid]

    depth = 1 - y / continuum

    # 找到最深的候选吸收位置
    center_index = np.argmax(depth)

    center = x[center_index]
    max_depth = depth[center_index]

    # 计算吸收面积
    area = np.trapezoid(depth, x)

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "候选吸收中心",
        f"{center:.1f} nm"
    )

    col2.metric(
        "最大相对吸收深度",
        f"{max_depth * 100:.2f}%"
    )

    col3.metric(
        "相对吸收面积",
        f"{area:.3f} nm"
    )

    # 绘制连续谱去除曲线
    fig3, ax3 = plt.subplots(figsize=(10, 4))

    ax3.plot(x, depth, label="Continuum-removed depth")
    ax3.axvline(center, linestyle="--", label="Candidate center")

    ax3.set_xlabel("Wavelength (nm)")
    ax3.set_ylabel("Relative absorption depth")
    ax3.set_title("Lunar Spectral Absorption Analysis")
    ax3.legend()
    ax3.grid(alpha=0.3)

    st.pyplot(fig3)

    st.caption(
        "教学用初步指标：采用区间端点线性连续谱。"
        "结果可能受波段边界、噪声及热辐射影响，"
        "不能直接解释为水含量。"
    )

else:
    st.warning("有效数据点不足，无法进行定量分析。")

# 实验结果导出
st.subheader("📥 导出科研实验结果")

import numpy as np

export_band = data[
    (data["Wavelength (nm)"] >= 2700) &
    (data["Wavelength (nm)"] <= 3100)
].copy()

if len(export_band) >= 3:

    export_x = export_band["Wavelength (nm)"].to_numpy()
    export_y = export_band["Signal"].to_numpy()

    # 建立线性连续谱
    export_continuum = np.linspace(
        export_y[0], export_y[-1], len(export_y)
    )

    valid = export_continuum > 0

    result = pd.DataFrame({
        "wavelength_nm": export_x[valid],
        "signal": export_y[valid],
        "continuum": export_continuum[valid],
        "relative_absorption_depth":
            1 - export_y[valid] / export_continuum[valid]
    })

    csv_data = result.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        label="⬇️ 下载光谱分析结果 CSV",
        data=csv_data,
        file_name=f"{sheet}_spectral_analysis.csv",
        mime="text/csv"
    )

else:
    st.warning("有效数据不足，暂时不能导出。")
