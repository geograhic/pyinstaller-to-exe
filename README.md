# PyInstaller-to-Exe

一个简化 PyInstaller 使用流程的工具，帮助您快速将 Python 脚本转换为独立的可执行文件（.exe）。

## 📋 简介

`pyinstaller-to-exe` 是一个便利工具，旨在简化使用 PyInstaller 打包 Python 应用程序的过程。它提供了一个用户友好的接口，使开发者能够轻松地将 Python 脚本编译成可独立运行的可执行文件，无需复杂的命令行操作。

## ✨ 主要功能

- 🔄 **一键打包**：简化 PyInstaller 的复杂参数配置
- 📦 **灵活配置**：支持自定义输出路径、图标、版本信息等
- 🎯 **批量处理**：支持同时处理多个 Python 脚本
- 💾 **配置保存**：保存打包配置以供后续使用
- 🛡️ **依赖管理**：自动检测和处理项目依赖
- 📝 **详细日志**：完整的打包过程日志输出

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/geograhic/pyinstaller-to-exe.git
cd pyinstaller-to-exe

# 安装依赖
pip install -r requirements.txt
```

### 基础用法

```bash
# 最简单的使用方式
python main.py --input your_script.py

# 指定输出路径
python main.py --input your_script.py --output ./dist/

# 添加图标和其他选项
python main.py --input your_script.py --icon app.ico --onefile
```

## 📖 详细文档

### 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--input` | Python 脚本路径（必需）| - |
| `--output` | 输出目录 | `./dist/` |
| `--icon` | 应用程序图标路径 | 无 |
| `--onefile` | 打包为单个可执行文件 | False |
| `--windowed` | 无控制台窗口（GUI 应用） | False |
| `--hidden-import` | 隐藏导入的模块 | - |
| `--version` | 指定版本号 | 无 |

### 配置文件

您也可以使用配置文件进行高级配置：

```yaml
# pyinstaller_config.yml
app_name: MyApp
main_script: app.py
output_dir: ./dist/
icon: ./assets/icon.ico
options:
  onefile: true
  windowed: true
  hidden_imports:
    - numpy
    - pandas
```

## 🔧 工作原理

1. **验证环境**：检查 PyInstaller 安装
2. **分析脚本**：扫描脚本依赖关系
3. **生成配置**：根据用户输入生成 PyInstaller 参数
4. **执行打包**：调用 PyInstaller 进行编译
5. **输出结果**：在指定目录生成可执行文件

## 💡 常见用例

### 打包 GUI 应用

```bash
python main.py --input gui_app.py --windowed --onefile --icon app.ico
```

### 打包数据科学应用

```bash
python main.py --input data_app.py --hidden-import numpy --hidden-import pandas --onefile
```

### 打包 Web 爬虫

```bash
python main.py --input crawler.py --onefile --hidden-import requests
```

## ⚠️ 注意事项

- 确保您的 Python 环境中已安装 PyInstaller：`pip install pyinstaller`
- 某些杀毒软件可能将生成的 .exe 文件标记为可疑，这是正常的
- 对于包含许多依赖的大型项目，编译时间可能较长
- 建议在虚拟环境中使用此工具

## 📦 依赖项

- Python 3.6+
- PyInstaller >= 4.0
- 其他依赖项见 `requirements.txt`

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 💬 联系与支持

- 📧 提交问题：[Issues](https://github.com/geograhic/pyinstaller-to-exe/issues)
- 🐛 报告 Bug：请详细描述问题和复现步骤
- 💡 功能建议：欢迎在 Discussions 中分享您的想法

## 🌟 致谢

感谢 PyInstaller 项目团队的出色工作，使 Python 应用程序的打包变得可能。

---

**⭐ 如果这个项目对您有帮助，请给我们一个 Star！**