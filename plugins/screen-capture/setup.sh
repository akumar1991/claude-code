#!/bin/bash
# Screen Capture Plugin Setup Script

set -e

echo "🖥️  Screen Capture Plugin Setup"
echo "================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Detect OS
OS="unknown"
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    OS="windows"
fi

echo -e "${BLUE}Detected OS: $OS${NC}"
echo ""

# Check Python
echo -e "${YELLOW}Checking Python...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓ Python found: $PYTHON_VERSION${NC}"
else
    echo -e "${RED}✗ Python 3 not found${NC}"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Check Node.js
echo -e "${YELLOW}Checking Node.js...${NC}"
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓ Node.js found: $NODE_VERSION${NC}"
else
    echo -e "${RED}✗ Node.js not found${NC}"
    echo "Please install Node.js 18 or higher"
    exit 1
fi

# Check npm
echo -e "${YELLOW}Checking npm...${NC}"
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo -e "${GREEN}✓ npm found: $NPM_VERSION${NC}"
else
    echo -e "${RED}✗ npm not found${NC}"
    exit 1
fi

echo ""

# Install Python dependencies
echo -e "${BLUE}Installing Python dependencies...${NC}"
if pip3 install -r requirements.txt; then
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠ Some Python dependencies may have failed${NC}"
fi

echo ""

# Install Node.js dependencies
echo -e "${BLUE}Installing Node.js dependencies...${NC}"
if npm install; then
    echo -e "${GREEN}✓ Node.js dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠ Some Node.js dependencies may have failed${NC}"
fi

echo ""

# Check for system dependencies
echo -e "${BLUE}Checking system dependencies...${NC}"

# Check Tesseract
if command -v tesseract &> /dev/null; then
    TESSERACT_VERSION=$(tesseract --version | head -n 1)
    echo -e "${GREEN}✓ Tesseract OCR found: $TESSERACT_VERSION${NC}"
else
    echo -e "${YELLOW}⚠ Tesseract OCR not found${NC}"
    echo ""
    echo "To use OCR features, install Tesseract:"
    if [[ "$OS" == "macos" ]]; then
        echo "  brew install tesseract"
        echo "  brew install tesseract-lang  # For additional languages"
    elif [[ "$OS" == "linux" ]]; then
        echo "  sudo apt-get install tesseract-ocr  # Debian/Ubuntu"
        echo "  sudo dnf install tesseract  # Fedora/RHEL"
        echo "  # For additional languages:"
        echo "  sudo apt-get install tesseract-ocr-fra tesseract-ocr-deu"
    fi
fi

# Check for Linux screen capture tools
if [[ "$OS" == "linux" ]]; then
    echo ""
    echo -e "${YELLOW}Checking Linux screen capture tools...${NC}"

    TOOLS_FOUND=0

    if command -v scrot &> /dev/null; then
        echo -e "${GREEN}✓ scrot found${NC}"
        TOOLS_FOUND=1
    fi

    if command -v gnome-screenshot &> /dev/null; then
        echo -e "${GREEN}✓ gnome-screenshot found${NC}"
        TOOLS_FOUND=1
    fi

    if command -v import &> /dev/null; then
        echo -e "${GREEN}✓ ImageMagick (import) found${NC}"
        TOOLS_FOUND=1
    fi

    if [[ $TOOLS_FOUND -eq 0 ]]; then
        echo -e "${YELLOW}⚠ No screen capture tools found${NC}"
        echo "Install at least one:"
        echo "  sudo apt-get install scrot gnome-screenshot imagemagick  # Debian/Ubuntu"
        echo "  sudo dnf install scrot gnome-screenshot ImageMagick  # Fedora/RHEL"
    fi
fi

echo ""

# Make scripts executable
echo -e "${BLUE}Making scripts executable...${NC}"
chmod +x scripts/*.py scripts/*.js hooks/*.py 2>/dev/null || true
echo -e "${GREEN}✓ Scripts are executable${NC}"

echo ""

# Create default output directories
echo -e "${BLUE}Creating output directories...${NC}"
mkdir -p screenshots error-screenshots session-screenshots write-screenshots
echo -e "${GREEN}✓ Output directories created${NC}"

echo ""

# Test installation
echo -e "${BLUE}Testing installation...${NC}"

# Test Python script
if python3 scripts/screen_capture.py list-monitors --json > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Python screen capture script works${NC}"
else
    echo -e "${YELLOW}⚠ Python screen capture script test failed${NC}"
fi

# Test Node script (just check it runs)
if node scripts/browser_capture.js --help > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Browser capture script works${NC}"
else
    echo -e "${YELLOW}⚠ Browser capture script test failed${NC}"
fi

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✓ Setup complete!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "Quick start:"
echo "  /screenshot              - Capture desktop"
echo "  /screenshot --analyze    - Capture and analyze"
echo "  /capture-web <url>       - Capture web page"
echo ""
echo "For more information, see README.md"
echo ""

# Check if in Claude Code environment
if [[ -n "$CLAUDE_CODE_SESSION" ]]; then
    echo -e "${BLUE}You're in a Claude Code session!${NC}"
    echo "The plugin is ready to use with slash commands."
else
    echo -e "${YELLOW}Note: Use these commands within Claude Code${NC}"
fi

echo ""
