
from pathlib import Path

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from scipy.signal import savgol_filter


# ==================================================
# 1. 页面设置
# ==================================================

st.set_page_config(
    page_title="GeoLunar AI 3.0",
    page_icon="🌕",
    layout="wide"
)

st.title("🌕 GeoLunar AI 3.0")
st.caption("Chang'e-6 Lunar Spectral Analysis Laboratory")

st.markdown(
    "真实光谱数据 · 多通道分析 · 光谱平滑 · "
    "吸收特征探索"
)

st.divider()


# ==================================================
# 2. 数据文件读取
# ==================================================

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data" / "raw"

DATA_DIR.mkdir(parents=True, exist_ok=True)

st.header("01 | 数据中心")

uploaded_file = st.file_uploader(
    "上传嫦娥六号 Excel 或 CSV",
    type=["xlsx", "xls", "csv"],
    key="upload_data"
)

local_files = (
    list(DATA_DIR.glob("*.xlsx"))
    + list(DATA_DIR.glob("*.xls"))
    + list(DATA_DIR.glob("*.csv"))
)

if uploaded_file is not None:
    source = uploaded_file
    file_name = uploaded_file.name

elif local_files:

    selected_file = st.selectbox(
        "选择本地数据文件",
        local_files,
        format_func=lambda p: p.name,
        key="local_file"
    )

    source = selected_file
    file_name = selected_file.name

else:
    st.warning(
        "没有找到数据文件。请上传文件，"
        "或将 Excel 放进 data/raw 文件夹。"
    )
    st.stop()


# ==================================================
# 3. 读取 Excel / CSV
# ==================================================

try:

    if file_name.lower().endswith(".csv"):

        raw_data = pd.read_csv(source)

        sheet_name = None

    else:

        excel = pd.ExcelFile(source)

        sheet_name = st.selectbox(
            "选择 Excel 工作表",
            excel.sheet_names,
            key="sheet_selector"
        )

        # 你的原始 Excel 字段名位于第二行
        raw_data = pd.read_excel(
            source,
            sheet_name=sheet_name,
            header=1
        )

except Exception as error:

    st.error(f"数据读取失败：{error}")
    st.stop()


# ==================================================
# 4. 清理列名
# ==================================================

raw_data.columns = [
    str(column).strip()
    for column in raw_data.columns
]

if raw_data.empty:

    st.error("数据表为空。")
    st.stop()


st.success(
    f"数据读取成功：{len(raw_data)} 行，"
    f"{len(raw_data.columns)} 列"
)

with st.expander("查看原始数据"):

    st.dataframe(
        raw_data.head(20),
        use_container_width=True
    )

with st.expander("查看全部字段名称"):

    st.write(list(raw_data.columns))


# ==================================================
# 5. 识别科学数据字段
# ==================================================

st.header("02 | 科学字段识别")

def find_column(columns, keyword):

    for column in columns:

        if keyword.lower() in str(column).lower():
            return column

    return None


identifier_col = find_column(
    raw_data.columns,
    "Identifier"
)

wavelength_col = find_column(
    raw_data.columns,
    "Center wavelength"
)

reflectance_col = find_column(
    raw_data.columns,
    "Reflectance with gap"
)

radiance_col = find_column(
    raw_data.columns,
    "Radiance"
)

if wavelength_col is None:

    st.error(
        "没有找到 Center wavelength 字段。"
        "请检查 Excel 表头是否正确。"
    )
    st.stop()

if identifier_col is None:

    st.error(
        "没有找到 Identifier 字段，"
        "无法自动分离 VIS、NIR、SWIR。"
    )
    st.stop()

if reflectance_col is None and radiance_col is None:

    st.error(
        "没有找到 Reflectance 或 Radiance 字段。"
    )
    st.stop()


st.write("自动识别结果：")

st.write({
    "Identifier": identifier_col,
    "波长": wavelength_col,
    "反射率": reflectance_col,
    "辐亮度": radiance_col
})


# ==================================================
# 6. 多通道分离
# ==================================================

st.header("03 | 多波段光谱分析")

raw_data[identifier_col] = (
    raw_data[identifier_col]
    .astype("string")
    .str.strip()
)

available_types = sorted(
    raw_data[identifier_col]
    .dropna()
    .unique()
    .tolist()
)

if not available_types:

    st.error("Identifier 中没有有效类型。")
    st.stop()


type_counts = (
    raw_data[identifier_col]
    .value_counts()
    .rename_axis("Identifier")
    .reset_index(name="数据行数")
)

st.subheader("观测类型统计")

st.dataframe(
    type_counts,
    use_container_width=True
)


selected_type = st.selectbox(
    "选择观测通道",
    available_types,
    key="channel_selector"
)

channel_data = raw_data[
    raw_data[identifier_col] == selected_type
].copy()

st.success(
    f"当前通道：{selected_type}，"
    f"共 {len(channel_data)} 行"
)


# ==================================================
# 7. 选择科学测量指标
# ==================================================

st.header("04 | 选择分析指标")

signal_options = {}

if reflectance_col is not None:
    signal_options["反射率 RADF"] = reflectance_col

if radiance_col is not None:
    signal_options["辐亮度 Radiance"] = radiance_col

signal_name = st.selectbox(
    "选择分析数据",
    list(signal_options.keys()),
    key="signal_selector"
)

signal_col = signal_options[signal_name]


# ==================================================
# 8. 数据清洗
# ==================================================

working = channel_data[
    [wavelength_col, signal_col]
].copy()

working[wavelength_col] = pd.to_numeric(
    working[wavelength_col],
    errors="coerce"
)

working[signal_col] = pd.to_numeric(
    working[signal_col],
    errors="coerce"
)

# 保留缺失值数量，用于数据质量检查
missing_count = working[signal_col].isna().sum()

# 去除无效波长和信号
working = working.dropna(
    subset=[wavelength_col, signal_col]
)

working = working[
    np.isfinite(working[wavelength_col])
    & np.isfinite(working[signal_col])
]

# 同一波长存在多个观测值时取平均
working = working.groupby(
    wavelength_col,
    as_index=False
)[signal_col].mean()

working = working.sort_values(
    wavelength_col
).reset_index(drop=True)

if len(working) < 5:

    st.error("有效数据点不足，无法进行分析。")
    st.stop()

x = working[wavelength_col].to_numpy(dtype=float)
y = working[signal_col].to_numpy(dtype=float)


# ==================================================
# 9. 数据质量检查
# ==================================================

st.header("05 | 数据质量检查")

minimum = float(x.min())
maximum = float(x.max())

spacing = np.diff(x)

uniform = np.allclose(
    spacing,
    spacing[0],
    rtol=1e-3,
    atol=1e-8
)

c1, c2, c3, c4 = st.columns(4)

c1.metric("有效数据点", len(x))
c2.metric("最小波长", f"{minimum:.2f} nm")
c3.metric("最大波长", f"{maximum:.2f} nm")
c4.metric("缺失信号记录", int(missing_count))

if uniform:

    st.success("当前波长间隔近似均匀。")

else:

    st.warning(
        "当前波长采样不均匀。"
        "SG 滤波按数据点序号计算，"
        "需要谨慎解释。"
    )


# ==================================================
# 10. 原始光谱
# ==================================================

st.header("06 | 原始光谱")

fig, ax = plt.subplots(figsize=(11, 4))

ax.plot(
    x,
    y,
    linewidth=1.5,
    label=signal_name
)

ax.set_xlabel("Center wavelength (nm)")
ax.set_ylabel(signal_name)

ax.set_title(
    f"{selected_type} - {signal_name}"
)

ax.grid(alpha=0.3)
ax.legend()

st.pyplot(fig)
plt.close(fig)


# ==================================================
# 11. 重点波段分析
# ==================================================

st.header("07 | 重点波段提取")

col1, col2 = st.columns(2)

with col1:

    band_min = st.number_input(
        "起始波长 (nm)",
        min_value=minimum,
        max_value=maximum,
        value=max(minimum, min(2700.0, maximum)),
        key="band_start"
    )

with col2:

    band_max = st.number_input(
        "结束波长 (nm)",
        min_value=minimum,
        max_value=maximum,
        value=maximum,
        key="band_end"
    )

if band_min >= band_max:

    st.warning("结束波长必须大于起始波长。")

    band_x = np.array([])
    band_y = np.array([])

else:

    mask = (
        (x >= band_min)
        & (x <= band_max)
    )

    band_x = x[mask]
    band_y = y[mask]

    if len(band_x) > 0:

        fig_band, ax_band = plt.subplots(
            figsize=(11, 4)
        )

        ax_band.plot(
            band_x,
            band_y,
            marker=".",
            linewidth=1.3
        )

        ax_band.set_xlabel("Wavelength (nm)")
        ax_band.set_ylabel(signal_name)

        ax_band.set_title(
            f"{selected_type} Selected Band"
        )

        ax_band.grid(alpha=0.3)

        st.pyplot(fig_band)
        plt.close(fig_band)

        st.metric(
            "当前波段数据点",
            len(band_x)
        )

    else:

        st.warning("当前波段没有有效数据。")


# ==================================================
# 12. SG 光谱平滑
# ==================================================

st.header("08 | SG 光谱平滑实验室")

st.write(
    "通过局部多项式拟合降低随机噪声，"
    "尽量保留光谱特征。"
)

max_window = min(
    51,
    len(y) if len(y) % 2 == 1 else len(y) - 1
)

y_smooth = y.copy()

if max_window >= 5:

    window = st.slider(
        "平滑窗口大小",
        min_value=5,
        max_value=max_window,
        value=min(11, max_window),
        step=2,
        key="sg_window_3"
    )

    poly = st.slider(
        "多项式阶数",
        min_value=1,
        max_value=min(5, window - 1),
        value=min(2, window - 1),
        key="sg_poly_3"
    )

    y_smooth = savgol_filter(
        y,
        window_length=window,
        polyorder=poly
    )

    fig_sg, ax_sg = plt.subplots(
        figsize=(11, 5)
    )

    ax_sg.plot(
        x,
        y,
        alpha=0.4,
        label="Original"
    )

    ax_sg.plot(
        x,
        y_smooth,
        linewidth=2,
        label="SG Smoothed"
    )

    ax_sg.set_xlabel("Wavelength (nm)")
    ax_sg.set_ylabel(signal_name)

    ax_sg.set_title("SG Smoothing Comparison")

    ax_sg.legend()
    ax_sg.grid(alpha=0.3)

    st.pyplot(fig_sg)
    plt.close(fig_sg)

    st.success("SG 平滑完成。")

else:

    st.warning("数据点不足，无法执行 SG 平滑。")


# ==================================================
# 13. 候选吸收谷检测
# ==================================================

st.header("09 | 候选吸收特征")

valley_indices = []

for i in range(1, len(y_smooth) - 1):

    if (
        y_smooth[i] < y_smooth[i - 1]
        and y_smooth[i] < y_smooth[i + 1]
    ):

        valley_indices.append(i)

if valley_indices:

    valleys = pd.DataFrame({
        "中心波长候选 (nm)": x[valley_indices],
        "信号值": y_smooth[valley_indices]
    })

    st.write(
        f"发现 {len(valleys)} 个候选局部低谷。"
    )

    st.dataframe(
        valleys,
        use_container_width=True
    )

else:

    st.info("没有检测到局部低谷。")


# ==================================================
# 14. 导出实验结果
# ==================================================

st.header("10 | 实验结果导出")

export_data = pd.DataFrame({
    "wavelength_nm": x,
    "original_signal": y,
    "smoothed_signal": y_smooth
})

csv_bytes = export_data.to_csv(
    index=False
).encode("utf-8-sig")

st.download_button(
    "⬇️ 下载当前通道分析 CSV",
    data=csv_bytes,
    file_name=f"GeoLunar_{selected_type}_results.csv",
    mime="text/csv",
    key="export_channel_csv"
)


# ==================================================
# 15. 科学说明
# ==================================================

st.divider()

st.header("11 | 科学说明")

st.info(
    """
    本程序是月球光谱数据探索工具。

    当前的局部低谷检测只是候选特征识别，
    不能直接认定为矿物吸收带。

    当前 SG 平滑使用数据点序号进行拟合，
    不均匀采样时应谨慎使用。

    反射率缺口、仪器响应、热辐射、
    波长校准和光度效应均可能影响结果。

    当前结果不能直接证明水或羟基存在，
    需要结合仪器资料、标准矿物光谱
    和其他科学证据进一步验证。
    """
)

st.caption(
    "GeoLunar AI 3.0 | Lunar Spectral Research"
)
