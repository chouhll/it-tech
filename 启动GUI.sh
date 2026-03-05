#!/bin/bash
set -e

# Markdown to PDF 转换器 - GUI 启动脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 启动 Markdown to PDF 转换器..."
echo ""

# 检查 Python 3 安装
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 未找到 Python 3，请先安装 Python 3.7 或更高版本${NC}"
    echo "  macOS: brew install python3"
    echo "  Linux: sudo apt install python3"
    exit 1
fi

# 显示 Python 版本
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✓ Python 版本: $PYTHON_VERSION"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo ""
    echo -e "${YELLOW}⚙️  首次运行，正在设置环境...${NC}"
    echo ""

    # 创建虚拟环境
    echo "1. 创建虚拟环境..."
    if ! python3 -m venv venv; then
        echo -e "${RED}❌ 创建虚拟环境失败${NC}"
        exit 1
    fi

    # 激活虚拟环境
    source venv/bin/activate

    # 升级 pip
    echo "2. 升级 pip..."
    pip install --upgrade pip -q

    # 安装依赖
    echo "3. 安装依赖包..."
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt -q
    else
        pip install reportlab markdown beautifulsoup4 lxml pygments -q
    fi

    echo ""
    echo -e "${GREEN}✅ 环境设置完成！${NC}"
    echo ""
else
    # 激活现有虚拟环境
    source venv/bin/activate
fi

# 检查必要的文件
if [ ! -f "md2pdf_gui.py" ]; then
    echo -e "${RED}❌ 找不到 md2pdf_gui.py 文件${NC}"
    exit 1
fi

if [ ! -f "md2pdf_reportlab.py" ]; then
    echo -e "${RED}❌ 找不到 md2pdf_reportlab.py 文件${NC}"
    exit 1
fi

# 启动 GUI
echo "启动图形界面..."
echo ""

# 根据操作系统选择启动方式
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS - 使用 pythonw 避免额外的终端窗口
    if command -v pythonw &> /dev/null; then
        pythonw md2pdf_gui.py
    else
        python md2pdf_gui.py
    fi
else
    # Linux/Windows
    python md2pdf_gui.py
fi

# 检查退出状态
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo -e "${RED}❌ 程序异常退出（退出码: $EXIT_CODE）${NC}"
    echo ""
    echo "常见问题："
    echo "  • 检查 Python 版本是否 >= 3.7"
    echo "  • 尝试删除 venv 文件夹后重新运行"
    echo "  • 检查是否有其他程序占用"
    echo ""
    echo "按任意键退出..."
    read -n 1
    exit $EXIT_CODE
fi
