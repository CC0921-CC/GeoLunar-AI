# GeoLunar-AI

An educational deep learning project for Earth and lunar resource exploration.



\# 🌕 GeoLunar AI



基于 Python 的月球光谱分析入门项目。



\## 1. 项目目标



利用月球光谱数据，探索波长与反射率之间的关系，

实现光谱可视化和初步吸收特征分析。



\## 2. 当前功能



\- Excel 光谱数据读取

\- 多样本选择

\- 光谱曲线绘制

\- 指定波段局部放大

\- 局部低谷自动检测

\- 连续谱去除

\- 吸收中心、深度和面积计算

\- CSV 分析结果导出



\## 3. 技术栈



\- Python

\- Pandas

\- NumPy

\- Matplotlib

\- Streamlit

\- OpenPyXL



\## 4. 如何运行



安装依赖：



```bash

py -m pip install pandas numpy openpyxl matplotlib streamlit

```



启动程序：



```bash

py -m streamlit run app.py

```



\## 5. 数据目录



原始 Excel 数据放在：



`data/raw/`



原始数据不随本仓库上传。



使用前请核实数据的公开来源、版本及使用许可。



\## 6. 科学注意事项



当前吸收特征分析采用简化的线性连续谱方法。



局部低谷不等于矿物鉴定结果，

吸收特征也不能直接等同于水的存在。



正式科研分析还需要考虑仪器校正、

热辐射、噪声、光度效应及其他干扰因素。



\## 7. 后续计划



\- 光谱平滑

\- 异常值检测

\- 连续谱去除优化

\- 矿物光谱特征对比

\- 月球资源勘查可视化



