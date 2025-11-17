# Screen Capture Plugin - Quick Reference

## Installation

```bash
cd plugins/screen-capture
./setup.sh
```

## Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/screenshot` | Capture desktop | `/screenshot --analyze` |
| `/capture-web` | Capture web page | `/capture-web https://example.com` |
| `/analyze-screenshot` | Analyze image | `/analyze-screenshot image.png --ocr` |

## Common Options

### Screenshot Options
- `--analyze` - AI analysis with vision
- `--ocr` - Extract text with OCR
- `--region x y w h` - Capture specific region
- Monitor number: `/screenshot 2`

### Web Capture Options
- `--fullpage` - Capture entire page (default)
- `--viewport WxH` - Set viewport size
- `--element selector` - Capture specific element
- `--extract` - Extract content (HTML, text, links)
- `--analyze` - Analyze the capture

### Analysis Options
- `--detailed` - Comprehensive analysis
- `--focus aspect` - Focus on: ui, design, accessibility, errors
- `--ocr` - Extract text
- `--lang code` - OCR language (eng, fra, deu, spa, etc.)

## Quick Workflows

### Bug Documentation
```bash
/screenshot --analyze --ocr
```

### Design Review
```bash
/capture-web http://localhost:3000 --fullpage
/analyze-screenshot ./screenshots/*.png --detailed --focus design
```

### Accessibility Check
```bash
/capture-web https://mysite.com
/analyze-screenshot ./screenshots/*.png --focus accessibility
```

### Extract Text from Image
```bash
/analyze-screenshot document.png --ocr --lang eng
```

### Capture Specific Element
```bash
/capture-web https://example.com --element "#pricing"
```

## Direct Script Usage

### Python (Desktop Capture)
```bash
# Capture screen
python3 scripts/screen_capture.py capture --json

# Capture region
python3 scripts/screen_capture.py region -x 0 -y 0 -w 1920 -h 1080

# OCR
python3 scripts/screen_capture.py ocr -i image.png --lang eng

# List monitors
python3 scripts/screen_capture.py list-monitors
```

### Node.js (Browser Capture)
```bash
# Capture page
node scripts/browser_capture.js page https://example.com --json

# Capture element
node scripts/browser_capture.js element https://example.com "#selector"

# Extract content
node scripts/browser_capture.js extract https://example.com -o content.json
```

## OCR Languages

| Language | Code | Language | Code |
|----------|------|----------|------|
| English | `eng` | Russian | `rus` |
| French | `fra` | Japanese | `jpn` |
| German | `deu` | Chinese (S) | `chi_sim` |
| Spanish | `spa` | Chinese (T) | `chi_tra` |
| Italian | `ita` | Arabic | `ara` |
| Portuguese | `por` | Korean | `kor` |

## Automation Hooks

Enable in `hooks/hooks.json`:

```json
{
  "auto_capture_on_error": {"enabled": true},
  "periodic_capture": {"enabled": true, "interval_minutes": 5},
  "capture_on_write": {"enabled": true, "file_patterns": ["*.tsx", "*.jsx"]}
}
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Screenshot fails | Check monitor: `list-monitors`, verify permissions |
| OCR inaccurate | Check language code, improve image quality |
| Browser fails | Install Puppeteer: `npm install puppeteer` |
| Permission denied | `chmod +x scripts/*.py scripts/*.js hooks/*.py` |

## Dependencies

### Python
```bash
pip3 install mss pillow pytesseract pyautogui
```

### System
```bash
# macOS
brew install tesseract

# Linux
sudo apt-get install tesseract-ocr scrot gnome-screenshot
```

### Node.js
```bash
npm install puppeteer commander
```

## File Structure

```
screen-capture/
├── .claude-plugin/
│   └── plugin.json          # Plugin metadata
├── commands/                # Slash commands
│   ├── screenshot.md
│   ├── capture-web.md
│   └── analyze-screenshot.md
├── agents/                  # AI agents
│   ├── screenshot-analyzer.md
│   └── ocr-extractor.md
├── hooks/                   # Automation hooks
│   ├── hooks.json
│   ├── auto_capture.py
│   ├── periodic_capture.py
│   └── capture_on_write.py
├── scripts/                 # Core scripts
│   ├── screen_capture.py   # Desktop capture & OCR
│   └── browser_capture.js  # Browser automation
├── examples/                # Examples and docs
│   ├── config.example.json
│   └── USAGE_EXAMPLES.md
├── README.md               # Full documentation
├── QUICKREF.md            # This file
├── setup.sh               # Installation script
├── requirements.txt       # Python dependencies
└── package.json          # Node.js dependencies
```

## Support

- Full docs: [README.md](README.md)
- Examples: [examples/USAGE_EXAMPLES.md](examples/USAGE_EXAMPLES.md)
- Issues: [GitHub](https://github.com/anthropics/claude-code/issues)
