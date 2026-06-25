# PyInstaller 打包工具 增强版

一个功能完整的 GUI 应用，帮助您快速将 Python 脚本打包成独立的 .exe 可执行文件。**直接运行 exe 即可使用，无需安装任何依赖！**

![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.6%2B-brightgreen)
![GUI](https://img.shields.io/badge/interface-GUI-blueviolet)

## 📋 简介

**PyInstaller 打包工具增强版** 是一个基于 Python Tkinter 的 GUI 应用程序，专为简化 PyInstaller 打包流程而设计。它提供了直观的用户界面，使您能够通过简单的点击操作将任何 Python 脚本打包成独立的 Windows 可执行文件。

## ✨ 核心特性

- **🎯 开箱即用** - 直接运行 exe 程序，无需配置，无需命令行
- **🔍 智能检测** - 自动检测系统中的 PyInstaller，支持多个 Python 环境
- **📁 便捷操作** - 集成文件浏览器和剪贴板支持，快速选择文件路径
- **💾 配置记忆** - 自动保存常用目录和设置，提升工作效率
- **🎨 图标定制** - 为生成的 exe 添加自定义图标（.ico 格式）
- **⚙️ 灵活选项** - 支持窗口程序模式、单文件打包等常用配置
- **📊 实时日志** - 完整显示打包过程和详细的错误信息
- **🛡️ 长路径支持** - 完美处理 Windows 超长路径问题（MAX_PATH 限制）

## 🚀 使用步骤

### 最快上手方式

1. **下载应用**
   - 从 [Releases](https://github.com/geograhic/pyinstaller-to-exe/releases) 下载最新的 exe 文件
   - 或克隆此仓库后自行打包成 exe

2. **启动应用**
   - 直接双击 `PyInstaller打包工具.exe` 启动
   - 应用会自动检测系统中的 PyInstaller

3. **配置打包**
   - **选择脚本**：点击「选择脚本」按钮，选择您要打包的 Python 文件（或从剪贴板粘贴路径）
   - **选择输出目录**：点击「选择输出」按钮，指定 exe 文件的保存位置
   - **设置 exe 名称**：自动根据脚本名称填充，也可自定义修改
   - **可选配置**：
     - 勾选「窗口程序模式」：生成的 exe 运行时不显示控制台窗口（适合 GUI 应用）
     - 点击「选择图标」：为 exe 添加自定义图标

4. **开始打包**
   - 点击「开始打包」按钮
   - 等待打包完成，实时查看底部日志
   - 打包成功后，exe 文件出现在输出目录中

## 🎯 使用场景

### GUI 应用打包
```
1. 选择使用 tkinter/PyQt/PySimpleGUI 等编写的 GUI 脚本
2. 勾选「窗口程序模式」（禁用控制台）
3. 可选：添加程序图标
4. 点击打包
```

### 数据处理工具打包
```
1. 选择 Python 脚本
2. 选择输出目录
3. 不勾选「窗口程序模式」（保留控制台用于显示结果）
4. 点击打包
```

### 独立工具发布
```
1. 选择脚本和输出目录
2. 勾选「窗口程序模式」
3. 添加程序图标
4. 打包后直接分发 exe 文件给用户
```

## 📖 界面说明

| 组件 | 说明 | 说明 |
|------|------|------|
| **常用工作目录** | 快速切换工作目录的下拉菜单 | 应用会自动记忆最近使用的 20 个目录 |
| **脚本路径** | 要打包的 Python 脚本文件 | 支持剪贴板粘贴路径 |
| **输出目录** | 生成的 exe 文件的保存位置 | 支持剪贴板粘贴路径 |
| **输出 exe 名称** | 生成的可执行文件名称 | 自动根据脚本名称填充，可手动修改 |
| **窗口程序模式** | 运行 exe 时是否显示控制台 | 勾选后无控制台（适合 GUI 应用） |
| **PyInstaller 位置** | 实际使用的 PyInstaller 路径 | 自动检测，也支��手动选择 |
| **图标路径** | exe 文件的自定义图标 | 需要 .ico 格式的图标文件 |

## ⚙️ PyInstaller 检测原理

应用会按以下优先级自动检测 PyInstaller：

1. **手动选择** - 用户从剪贴板粘贴或手动选择的 pyinstaller.exe
2. **Python Scripts 目录** - `{Python安装路径}\Scripts\pyinstaller.exe`
3. **系统 PATH** - 系统环境变量中配置的 pyinstaller 命令
4. **当前 Python 环境** - 当前 Python 的 PyInstaller 模块
5. **其他 Python 环境** - 系统中其他 Python 环境的 PyInstaller

若自动检测失败，点击「重新检测 PyInstaller」按钮或手动选择 pyinstaller.exe 文件。

## 💾 数据存储

应用会自动保存以下信息：

- 最近使用的脚本路径
- 最近使用的输出目录  
- 最近使用的图标路径
- 常用工作目录列表（最多 20 个）
- 手动选择的 PyInstaller 路径

**配置文件位置：**
- Windows: `%APPDATA%\PyInstaller打包工具\settings.json`
- macOS/Linux: `~/.PyInstaller打包工具/settings.json`

## 🔧 打包参数

应用使用以下 PyInstaller 参数进行打包：

```
--onefile          # 打包为单个可执行文件
--clean            # 清理中间文件
--noconfirm        # 无确认覆盖
--noconsole        # （条件）隐藏控制台窗口
--icon             # （条件）指定图标
--distpath         # 输出目录
--workpath         # 临时工作目录
--specpath         # .spec 文件目录
```

## 🛠️ 高级用法

### 命令行自检

检查 PyInstaller 配置状态：

```bash
python "使用pyinstaller将py打包成exe1.5_增强版_v20260518.py" --self-check
```

### 源码运行

直接运行 Python 脚本（需要 Python 环境）：

```bash
python "使用pyinstaller将py打包成exe1.5_增强版_v20260518.py"
```

### 打包本工具成 exe

```bash
pyinstaller --onefile --noconsole --icon icon.ico \
  "使用pyinstaller将py打包成exe1.5_增强版_v20260518.py"
```

## ⚠️ 常见问题

### Q: 启动时提示"未检测到 PyInstaller"怎么办？

**A:** 需要先安装 PyInstaller：
```bash
pip install pyinstaller
```
安装后重启应用或点击「重新检测 PyInstaller」按钮。

### Q: 打包后的 exe 很大，如何减小体积？

**A:** 
- 在虚拟环境中仅安装必要的依赖包
- 使用 UPX 进行压缩（需要额外配置 PyInstaller）
- 合理选择打包参数

### Q: 打包后的 exe 被杀毒软件报警？

**A:** 这是常见的误报问题。PyInstaller 生成的 exe 是完全安全的。可以：
- 在杀毒软件中添加信任
- 向杀毒软件厂商报告误报

### Q: 打包包含数据文件的应用如何处理？

**A:** PyInstaller 会自动打包脚本同目录的文件。对于需要在打包后访问的数据文件，在 Python 脚本中使用：

```python
import sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    # 打包后的环境
    base_path = sys._MEIPASS
else:
    # 开发环境
    base_path = Path(__file__).parent

data_file = Path(base_path) / 'data' / 'config.json'
```

### Q: 打包失败，日志显示找不到模块怎么办？

**A:** 某些模块需要手动指定。两个解决方案：
1. 使用命令行：`pip install 模块名`
2. 确保脚本能在 Python 环境中直接运行

### Q: 是否支持打包 64 位或 32 位应用？

**A:** 应用会根据运行环境的 Python 版本自动确定。若需要不同架构，请用对应版本的 Python 运行。

## 📦 系统要求

- **操作系统**：Windows 7 或更高版本
- **Python**：3.6 或更高版本（用于打包）
- **PyInstaller**：4.0 或更高版本

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建功能分支（`git checkout -b feature/AmazingFeature`）
3. 提交更改（`git commit -m 'Add some AmazingFeature'`）
4. 推送到分支（`git push origin feature/AmazingFeature`）
5. 开启 Pull Request

## 💬 反馈与支持

- 📧 [提交 Issue](https://github.com/geograhic/pyinstaller-to-exe/issues)
- 🐛 报告 Bug：请提供操作步骤、错误信息和系统环境
- 💡 功能建议：欢迎分享您的想法和需求

## 📋 更新日志

### v1.5 增强版

- ✅ 图形化界面（GUI），无需命令行
- ✅ 自动检测多个 Python 环境中的 PyInstaller
- ✅ 界面显示 PyInstaller 的实际位置和版本
- ✅ Windows 长路径支持，解决 MAX_PATH 限制问题
- ✅ 路径输入框支持超长路径显示和复制
- ✅ 剪贴板路径粘贴功能
- ✅ 完整的配置记忆和自动恢复
- ✅ 实时打包日志显示
- ✅ 支持自定义图标和输出目录
- ✅ 窗口程序模式选项

---

**⭐ 如果这个工具对您有帮助，请给个 Star！**
