# Automated eCommerce Scene Composer 🎨
**一款专为电商设计的自动化产品视觉合成工具**
<img width="2369" height="1331" alt="Screenshot 2026-01-19 172354" src="https://github.com/user-attachments/assets/1e39c760-ee31-4a55-9afb-640de5079b83" />


## 📖 简介 / Introduction
**Automated eCommerce Scene Composer** 是一款高效的自动化视觉合成脚本。它能够将海量的白底产品图（ASINs）批量合成为具有专业光影感的海报。

- **中文用户**：适用于需要快速生成双11、大促海报的电商运营或技术人员。
- **English Users**: A high-efficiency tool to batch-compose product photos into high-quality podium backgrounds with dynamic recoloring and shadow rendering.
---

## ✨ 核心特性 / Features
- **🚀 全自动化 / Batch Processing**: 支持多活动（如双11、情人节）、多类目的全自动并行合成。
- **🎨 智能色彩融合 / Smart Recoloring**: 采用 HSV 空间偏移与**垂直渐变蒙版 (Gradient Mask)** 技术，改变背景色时完美保留展台原有的细节与纹理。
- **🔦 真实双层阴影 / Realistic Shadows**:
  - **AO 接触阴影**: 定义轮廓，消除漂浮感。
  - **柔和落地阴影**: 增强空间深度感。
- **📐 动态布局 / Dynamic Layout**: 自动定位展台锚点，支持通过配置文件动态控制缩放比例与标题位置。
---

## 📂 目录结构 / Directory Structure

```text
.
├── main.py                 # 程序主入口 / Main Entry
├── background.jpg          # 背景模板 / Podium Template
├── events/                 # 活动目录 / Events Root
│   ├── double11/           # 活动 A / Event A
│   │   ├── config.txt      # 参数配置 / Configuration
│   │   └── asins/          # 产品图片 / Product Images
│   │       ├── Shoes/      # 类目 / Categories
│   │       └── Bags/
│   └── valentines/         # 活动 B / Event B
└── output/                 # 合成结果 / Final Output
```
## ⚙️ 配置说明 / Configuration (config.txt)
```
# --- 背景变色 / Background Recoloring (Old RGB : New HEX) ---
color_map_1: 203,181,157 : #F8BBD0

# --- 标题排版 / Text Layout (Ratio 0.0 - 1.0) ---
main_title: New Spring Arrivals
main_title_size: 0.08
main_title_pos: 0.5, 0.1

sub_title: 2026 Collection 50% OFF
sub_title_size: 0.04
sub_title_pos: 0.5, 0.18

text_color: #FFFFFF

# --- 产品缩放 / Scale ---
asin_scale: 0.35
```
## 🚀 快速开始 / Quick Start
```
安装依赖 / Install Dependencies: Bash - pip install opencv-python pillow numpy
准备资源 / Setup: 将产品图按目录结构放入 asins 文件夹，修改 config.txt。
运行 / Run: Bash - python main.py
```

## 🛠️ 技术细节 / Technical Details
本项目采用了 Smart Soft-Blending 算法。不同于简单的透明度叠加，它通过计算产品底部与背景的色差，动态补充两层阴影蒙版，确保即使在浅色背景下，浅色产品依然具有极高的辨识度与立体感。
