# Screen Capture & Analysis Plugin

A comprehensive Claude Code plugin for capturing, analyzing, and extracting information from screens, browsers, and applications.

## Features

### 🖥️ Desktop Screen Capture
- Capture full screen or specific monitors
- Capture specific screen regions
- Cross-platform support (macOS, Linux, Windows)
- High-quality PNG and JPEG output

### 🌐 Browser Automation
- Capture full web pages using Puppeteer
- Capture specific elements by CSS selector
- Extract page content (HTML, text, links, images)
- Custom viewport sizes for responsive testing
- JavaScript enable/disable control

### 🔍 AI-Powered Analysis
- Visual analysis using Claude's vision capabilities
- UI/UX evaluation and design critique
- Accessibility audits (WCAG compliance)
- Error detection and bug identification
- Detailed or focused analysis modes

### 📝 OCR Text Extraction
- Extract text from screenshots using Tesseract OCR
- Multi-language support (30+ languages)
- Confidence scoring
- Structured data extraction

### ⚡ Automation Hooks
- Auto-capture on errors
- Periodic session captures
- Capture after file writes
- Configurable triggers

## Installation

### 1. Enable the Plugin

The plugin is located in the `plugins/screen-capture` directory of your Claude Code installation.

### 2. Install Python Dependencies

```bash
cd plugins/screen-capture
pip3 install -r requirements.txt
```

**Required packages:**
- `mss` - Fast cross-platform screen capture
- `Pillow` - Image processing
- `pytesseract` - OCR wrapper for Tesseract
- `pyautogui` - GUI automation (fallback)

### 3. Install System Dependencies

**OCR (Tesseract):**

```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Additional languages (optional)
brew install tesseract-lang  # macOS
sudo apt-get install tesseract-ocr-fra tesseract-ocr-deu  # Ubuntu
```

**Linux screen capture tools:**

```bash
# Ubuntu/Debian
sudo apt-get install scrot gnome-screenshot imagemagick

# Fedora/RHEL
sudo dnf install scrot gnome-screenshot ImageMagick
```

### 4. Install Node.js Dependencies

```bash
cd plugins/screen-capture
npm install
```

**Required packages:**
- `puppeteer` - Browser automation
- `commander` - CLI argument parsing

### 5. Verify Installation

```bash
# Test Python capture
python3 scripts/screen_capture.py list-monitors

# Test browser capture
node scripts/browser_capture.js page https://example.com --help

# Test OCR
python3 scripts/screen_capture.py ocr -i test_image.png
```

## Quick Start

### Basic Commands

```bash
# Capture desktop screenshot
/screenshot

# Capture and analyze
/screenshot --analyze

# Capture with OCR
/screenshot --ocr

# Capture web page
/capture-web https://example.com

# Analyze existing screenshot
/analyze-screenshot ./screenshot.png --detailed
```

## Commands

### `/screenshot` - Desktop Screenshot

Capture desktop screenshots with optional analysis and OCR.

**Usage:**
```bash
/screenshot [monitor] [--analyze] [--ocr] [--region x y w h]
```

**Examples:**
```bash
/screenshot                    # Capture primary monitor
/screenshot 2                  # Capture monitor 2
/screenshot --analyze          # Capture and analyze
/screenshot --ocr              # Capture and extract text
/screenshot --region 0 0 1920 1080  # Capture region
```

**Options:**
- `monitor` - Monitor number (default: 1)
- `--analyze` - Analyze screenshot with Claude's vision
- `--ocr` - Extract text using OCR
- `--region x y w h` - Capture specific region
- `--output path` - Custom output path

### `/capture-web` - Web Page Capture

Capture web pages using browser automation.

**Usage:**
```bash
/capture-web <url> [options]
```

**Examples:**
```bash
/capture-web https://example.com
/capture-web https://example.com --viewport 1920x1080
/capture-web https://example.com --element "#main"
/capture-web https://example.com --extract
/capture-web https://example.com --analyze
```

**Options:**
- `--fullpage` - Capture entire page (default: true)
- `--viewport WxH` - Viewport size (default: 1920x1080)
- `--element selector` - Capture specific element
- `--wait-for selector` - Wait for element before capture
- `--wait ms` - Additional wait time
- `--format png|jpeg` - Output format
- `--no-javascript` - Disable JavaScript
- `--extract` - Extract content instead of screenshot
- `--analyze` - Analyze the screenshot
- `--output path` - Custom output path

### `/analyze-screenshot` - Analyze Screenshot

Analyze screenshots with AI vision and OCR.

**Usage:**
```bash
/analyze-screenshot <image-path> [options]
```

**Examples:**
```bash
/analyze-screenshot ./screenshot.png
/analyze-screenshot ./screenshot.png --detailed
/analyze-screenshot ./screenshot.png --ocr
/analyze-screenshot ./screenshot.png --focus ui
/analyze-screenshot ./screenshot.png --ocr --lang fra
```

**Options:**
- `--ocr` - Perform OCR text extraction
- `--detailed` - Comprehensive analysis
- `--lang code` - OCR language (default: eng)
- `--focus aspect` - Focus on: ui, text, design, accessibility, errors

## Agents

### Screenshot Analyzer Agent

Expert at analyzing screenshots, UI designs, and visual content.

**Capabilities:**
- Visual analysis and description
- UI/UX evaluation
- Design critique and recommendations
- Accessibility review (WCAG compliance)
- Error detection and bug identification
- Layout and structure analysis

**Invoke:**
```bash
# The agent is automatically used by /analyze-screenshot
# Or invoke directly:
/task Use the screenshot-analyzer agent to review this UI
```

### OCR Extractor Agent

Specialized in extracting and analyzing text from images.

**Capabilities:**
- Text extraction using Tesseract OCR
- Multi-language support
- Structured data parsing (tables, lists, forms)
- Quality assessment
- Content formatting

**Invoke:**
```bash
# Automatically used with --ocr flag
/analyze-screenshot image.png --ocr

# Or invoke directly for batch processing:
/task Use ocr-extractor agent to process all images in ./screenshots/
```

## Hooks

Hooks enable automatic screenshot capture based on events.

### Configuration

Edit `plugins/screen-capture/hooks/hooks.json` to enable/configure hooks.

### Auto-Capture on Error

Automatically capture screenshots when errors occur.

**Configuration:**
```json
{
  "auto_capture_on_error": {
    "enabled": true,
    "analyze": true,
    "ocr": false,
    "output_dir": "./error-screenshots"
  }
}
```

**Use Case:** Debugging - automatically capture screen state when errors happen.

### Periodic Capture

Capture screenshots at regular intervals during development.

**Configuration:**
```json
{
  "periodic_capture": {
    "enabled": true,
    "interval_minutes": 5,
    "max_captures_per_session": 20,
    "output_dir": "./session-screenshots"
  }
}
```

**Use Case:** Session recording - create a visual timeline of your work.

### Capture on Write

Capture screenshots after writing specific files (e.g., UI files).

**Configuration:**
```json
{
  "capture_on_write": {
    "enabled": true,
    "file_patterns": ["*.html", "*.css", "*.tsx", "*.jsx"],
    "analyze": false,
    "output_dir": "./write-screenshots"
  }
}
```

**Use Case:** Visual regression - track UI changes as you edit files.

## Direct Script Usage

### Desktop Capture Script

```bash
# Capture screen
python3 scripts/screen_capture.py capture -m 1 --json

# Capture region
python3 scripts/screen_capture.py region -x 0 -y 0 -w 1920 -h 1080

# OCR on image
python3 scripts/screen_capture.py ocr -i screenshot.png --lang eng

# List monitors
python3 scripts/screen_capture.py list-monitors
```

**Options:**
- `capture` - Capture full screen or monitor
- `region` - Capture specific region
- `ocr` - Extract text from image
- `list-monitors` - List available monitors
- `-m, --monitor` - Monitor number
- `-o, --output` - Output file path
- `-d, --dir` - Output directory
- `-l, --lang` - OCR language
- `--json` - JSON output format

### Browser Capture Script

```bash
# Capture web page
node scripts/browser_capture.js page https://example.com --json

# Capture element
node scripts/browser_capture.js element https://example.com "#selector"

# Extract content
node scripts/browser_capture.js extract https://example.com -o content.json
```

**Options:**
- `page <url>` - Capture full page
- `element <url> <selector>` - Capture specific element
- `extract <url>` - Extract page content
- `-w, --width` - Viewport width
- `-h, --height` - Viewport height
- `--no-fullpage` - Capture viewport only
- `-s, --selector` - Wait for selector
- `-t, --wait` - Additional wait time (ms)
- `-f, --format` - Output format (png, jpeg)
- `--no-javascript` - Disable JavaScript
- `--json` - JSON output format

## OCR Languages

Common language codes for OCR:

| Language | Code |
|----------|------|
| English | `eng` |
| French | `fra` |
| German | `deu` |
| Spanish | `spa` |
| Italian | `ita` |
| Portuguese | `por` |
| Russian | `rus` |
| Japanese | `jpn` |
| Chinese (Simplified) | `chi_sim` |
| Chinese (Traditional) | `chi_tra` |
| Arabic | `ara` |
| Korean | `kor` |

**Install additional languages:**

```bash
# macOS
brew install tesseract-lang

# Ubuntu/Debian
sudo apt-get install tesseract-ocr-fra tesseract-ocr-deu tesseract-ocr-spa
```

## Use Cases

### 1. UI Bug Documentation

Capture and analyze UI bugs with automatic screenshots:

```bash
# Capture bug
/screenshot --analyze

# Extract error messages
/screenshot --ocr

# Analyze error screen
/analyze-screenshot error.png --focus errors
```

### 2. Design Review

Review and critique designs:

```bash
# Capture design
/capture-web http://localhost:3000 --fullpage

# Detailed design analysis
/analyze-screenshot ./screenshots/*.png --detailed --focus design
```

### 3. Accessibility Audit

Check for accessibility issues:

```bash
# Capture pages
/capture-web https://myapp.com --fullpage

# Accessibility-focused analysis
/analyze-screenshot ./screenshots/*.png --detailed --focus accessibility
```

### 4. Competitive Analysis

Analyze competitor interfaces:

```bash
# Capture competitor site
/capture-web https://competitor.com --fullpage

# Extract content
/capture-web https://competitor.com --extract

# Analyze design and UX
/analyze-screenshot ./screenshots/*.png --detailed
```

### 5. Documentation

Create visual documentation:

```bash
# Capture application states
/screenshot

# Analyze and describe
/analyze-screenshot ./screenshots/*.png

# Extract UI text
/screenshot --ocr
```

### 6. Error Investigation

Debug issues with automatic capture:

```bash
# Enable auto-capture on errors in config
# Errors automatically captured to ./error-screenshots/

# Review and analyze
/analyze-screenshot ./error-screenshots/*.png --ocr
```

## Configuration

### Global Configuration

Create or edit `.claude-code/config.json`:

```json
{
  "plugins": {
    "screen-capture": {
      "default_output_dir": "./screenshots",
      "auto_analyze": false,
      "auto_ocr": false
    }
  }
}
```

### Hook Configuration

Edit `plugins/screen-capture/hooks/hooks.json` to configure automatic capturing.

See [examples/config.example.json](examples/config.example.json) for all options.

## Troubleshooting

### Screenshots Not Working

**Issue:** Screenshots fail or produce black images

**Solutions:**
1. Check monitor number: `/screenshot list-monitors`
2. Verify screen recording permissions (macOS)
3. Try different capture method
4. Install platform-specific tools (scrot, gnome-screenshot)

### OCR Not Accurate

**Issue:** OCR produces garbled or incorrect text

**Solutions:**
1. Verify Tesseract installation: `tesseract --version`
2. Try correct language code: `--lang fra` for French
3. Improve image quality (higher resolution, better contrast)
4. Use proper DPI (300+ recommended)

### Browser Capture Fails

**Issue:** Puppeteer fails to launch or capture

**Solutions:**
1. Install dependencies: `npm install puppeteer`
2. Increase timeout: `--wait 5000`
3. Check URL accessibility
4. Verify Node.js version (18+)

### Dependencies Missing

**Issue:** Import errors or command not found

**Solutions:**

```bash
# Install Python dependencies
pip3 install -r requirements.txt

# Install Node dependencies
npm install

# Install system dependencies
brew install tesseract  # macOS
sudo apt-get install tesseract-ocr scrot  # Linux
```

### Permissions Issues

**Issue:** Permission denied errors

**Solutions:**

```bash
# Make scripts executable
chmod +x scripts/*.py scripts/*.js hooks/*.py

# macOS: Grant screen recording permission
# System Preferences → Security & Privacy → Screen Recording
```

## Performance Tips

1. **Format Selection:** Use PNG for text/UI, JPEG for photos
2. **Full Page Captures:** Can be slow, use viewport when possible
3. **Batch Operations:** Run captures in parallel
4. **OCR:** Slower than vision, use only when exact text needed
5. **Browser Headless:** Faster than headed mode

## Examples

See [examples/USAGE_EXAMPLES.md](examples/USAGE_EXAMPLES.md) for comprehensive usage examples and workflows.

## Contributing

Contributions welcome! Areas for improvement:

- Video capture support
- Additional OCR engines (EasyOCR, PaddleOCR)
- Mobile device capture (iOS, Android)
- PDF generation from screenshots
- Image comparison and diff tools
- Cloud storage integration

## License

MIT License - see LICENSE file for details

## Support

- **Issues:** [GitHub Issues](https://github.com/anthropics/claude-code/issues)
- **Discussions:** [GitHub Discussions](https://github.com/anthropics/claude-code/discussions)
- **Documentation:** [Claude Code Docs](https://docs.claude.com)

## Version History

### 1.0.0 (Initial Release)
- Desktop screen capture (cross-platform)
- Browser automation with Puppeteer
- OCR text extraction (Tesseract)
- AI-powered analysis agents
- Automation hooks
- Multi-language support
- Comprehensive documentation

---

**Made with ❤️ for Claude Code**
