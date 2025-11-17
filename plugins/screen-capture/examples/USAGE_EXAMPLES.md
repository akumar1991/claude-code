# Screen Capture Plugin - Usage Examples

This document provides practical examples of using the Screen Capture plugin.

## Quick Start

### Basic Desktop Screenshot

```bash
# Capture primary monitor
/screenshot

# Capture specific monitor
/screenshot 2

# Capture and analyze
/screenshot --analyze

# Capture and extract text
/screenshot --ocr
```

### Web Page Capture

```bash
# Capture full web page
/capture-web https://example.com

# Capture with custom viewport
/capture-web https://example.com --viewport 1920x1080

# Capture specific element
/capture-web https://example.com --element "#main-content"

# Extract page content
/capture-web https://example.com --extract
```

### Analyze Existing Screenshots

```bash
# Basic analysis
/analyze-screenshot ./screenshot.png

# Detailed analysis
/analyze-screenshot ./screenshot.png --detailed

# Extract text with OCR
/analyze-screenshot ./screenshot.png --ocr

# Focused analysis on UI
/analyze-screenshot ./screenshot.png --detailed --focus ui
```

## Common Workflows

### Workflow 1: UI Bug Documentation

When you encounter a UI bug, document it with screenshots and analysis:

```bash
# 1. Capture the bug
/screenshot --analyze

# Claude will capture and provide analysis like:
# - What's visible
# - Potential issues
# - Suggested fixes

# 2. Extract any error messages
/screenshot --ocr

# 3. Capture additional context (e.g., console)
/screenshot --region 0 800 1920 280
```

### Workflow 2: Competitive Analysis

Analyze competitor websites:

```bash
# 1. Capture competitor homepage
/capture-web https://competitor.com --fullpage

# 2. Analyze the design
/analyze-screenshot ./screenshots/webpage_*.png --detailed --focus design

# 3. Extract specific sections
/capture-web https://competitor.com --element ".pricing-section"

# 4. Extract content for reference
/capture-web https://competitor.com --extract
```

### Workflow 3: Documentation Creation

Create documentation with screenshots:

```bash
# 1. Capture application state
/screenshot

# 2. Analyze and get descriptions
/analyze-screenshot ./screenshots/*.png

# 3. Extract UI text for documentation
/screenshot --ocr

# 4. Organize by feature
# Screenshots automatically timestamped for easy organization
```

### Workflow 4: Accessibility Audit

Check your application for accessibility issues:

```bash
# 1. Capture key pages
/capture-web http://localhost:3000 --fullpage
/capture-web http://localhost:3000/dashboard --fullpage

# 2. Analyze with accessibility focus
/analyze-screenshot ./screenshots/webpage_*.png --detailed --focus accessibility

# Claude will check:
# - Color contrast
# - Text size
# - Touch target sizes
# - Focus indicators
# - Alt text (if visible)
```

### Workflow 5: Error Investigation

When debugging errors:

```bash
# Enable auto-capture on errors (in config)
# Edit plugins/screen-capture/hooks/hooks.json
# Set auto_capture_on_error.enabled = true

# Now whenever an error occurs, screenshots are automatically captured

# Review error screenshots
/analyze-screenshot ./error-screenshots/*.png --ocr

# Extract stack traces
/screenshot --ocr
```

## Direct Script Usage

You can also use the scripts directly:

### Desktop Capture Script

```bash
# Basic capture
python3 plugins/screen-capture/scripts/screen_capture.py capture

# Capture specific monitor
python3 plugins/screen-capture/scripts/screen_capture.py capture -m 2

# Capture region
python3 plugins/screen-capture/scripts/screen_capture.py region \
  -x 0 -y 0 -w 1920 -h 1080

# OCR on image
python3 plugins/screen-capture/scripts/screen_capture.py ocr \
  -i screenshot.png

# List monitors
python3 plugins/screen-capture/scripts/screen_capture.py list-monitors

# JSON output
python3 plugins/screen-capture/scripts/screen_capture.py capture --json
```

### Browser Capture Script

```bash
# Capture web page
node plugins/screen-capture/scripts/browser_capture.js page https://example.com

# Capture specific element
node plugins/screen-capture/scripts/browser_capture.js element \
  https://example.com "#main-content"

# Extract content
node plugins/screen-capture/scripts/browser_capture.js extract \
  https://example.com --output content.json

# Custom viewport and wait
node plugins/screen-capture/scripts/browser_capture.js page \
  https://example.com \
  --width 1920 --height 1080 \
  --selector ".loaded-indicator" \
  --wait 2000

# JSON output
node plugins/screen-capture/scripts/browser_capture.js page \
  https://example.com --json
```

## Advanced Examples

### Multi-Language OCR

```bash
# Extract text in French
/analyze-screenshot ./french_doc.png --ocr --lang fra

# Extract text in Japanese
/analyze-screenshot ./japanese_ui.png --ocr --lang jpn

# Extract text in Chinese (Simplified)
/analyze-screenshot ./chinese_doc.png --ocr --lang chi_sim
```

### Mobile Viewport Capture

```bash
# Capture as iPhone
/capture-web https://example.com --viewport 375x812

# Capture as iPad
/capture-web https://example.com --viewport 768x1024

# Capture as Android
/capture-web https://example.com --viewport 360x640
```

### Batch Analysis

Using bash loops to analyze multiple screenshots:

```bash
# Analyze all screenshots in directory
for img in ./screenshots/*.png; do
  /analyze-screenshot "$img" --ocr
done

# Analyze web pages
for url in https://example.com https://example.org; do
  /capture-web "$url" --analyze
done
```

### Automated Testing Workflow

```bash
# 1. Run your application
npm run dev &

# Wait for startup
sleep 5

# 2. Capture baseline screenshots
/capture-web http://localhost:3000 --fullpage
/capture-web http://localhost:3000/dashboard --fullpage

# 3. Make changes to your code
# ... edit files ...

# 4. Capture new screenshots
/capture-web http://localhost:3000 --fullpage

# 5. Compare and analyze
/analyze-screenshot ./screenshots/*.png --detailed
```

### Content Extraction and Analysis

```bash
# 1. Extract page content
/capture-web https://example.com --extract

# 2. Analyze the structure
# Claude analyzes the JSON output showing:
# - Page title and URL
# - All links and navigation
# - All images
# - Full text content

# 3. Use for further processing
# The extracted content can be saved and processed
```

## Integration with Other Tools

### With Git Workflow

```bash
# Before committing UI changes, capture and analyze
/screenshot --analyze
/capture-web http://localhost:3000 --analyze

# Add screenshots to commit
git add ./screenshots/*.png
git commit -m "feat: new dashboard layout

See screenshots for visual reference"
```

### With Testing

```bash
# Capture test results
npm test
/screenshot

# Analyze test output
/analyze-screenshot ./screenshots/*.png --ocr
```

### With CI/CD

```bash
# In CI pipeline, capture deployment previews
/capture-web https://preview.example.com --fullpage
/analyze-screenshot ./screenshots/*.png --detailed

# Store screenshots as artifacts
```

## Tips and Tricks

### 1. **Organized Storage**

Create dated directories:

```bash
mkdir -p screenshots/$(date +%Y-%m-%d)
/screenshot --output screenshots/$(date +%Y-%m-%d)/feature-xyz.png
```

### 2. **Quick Error Documentation**

Alias for quick bug capture:

```bash
alias bug-capture="/screenshot --analyze --ocr"
```

### 3. **Batch Web Captures**

Create a URL list file and capture all:

```bash
# urls.txt contains one URL per line
while read url; do
  /capture-web "$url" --fullpage
done < urls.txt
```

### 4. **OCR for Code Screenshots**

When someone sends you a code screenshot:

```bash
/analyze-screenshot code_screenshot.png --ocr

# Extract the code, then save it
# (Claude will format the extracted code properly)
```

### 5. **Design Review Workflow**

```bash
# 1. Capture design
/capture-web http://localhost:3000 --fullpage

# 2. Get detailed design analysis
/analyze-screenshot ./screenshots/*.png --detailed --focus design

# 3. Generate feedback report
# Claude provides structured feedback on:
# - Layout and spacing
# - Typography
# - Color scheme
# - Consistency
# - Improvements
```

## Troubleshooting

### Python Dependencies Missing

```bash
# Install all Python dependencies
pip install mss pillow pytesseract pyautogui

# Install Tesseract OCR (system package)
# macOS:
brew install tesseract

# Ubuntu/Debian:
sudo apt-get install tesseract-ocr

# Windows:
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

### Node.js Dependencies Missing

```bash
# Install Puppeteer
cd plugins/screen-capture
npm install puppeteer

# Or install globally
npm install -g puppeteer
```

### Screenshot Not Working

```bash
# Check available monitors
python3 plugins/screen-capture/scripts/screen_capture.py list-monitors

# Try different monitor
/screenshot 1
/screenshot 2

# Check permissions (macOS)
# System Preferences → Security & Privacy → Screen Recording
```

### OCR Not Accurate

```bash
# Try different language
/analyze-screenshot image.png --ocr --lang fra

# Improve image quality first
# Use higher resolution screenshots
# Ensure good contrast

# Check Tesseract installation
tesseract --version
```

## Performance Tips

1. **PNG vs JPEG**: Use PNG for text/UI, JPEG for photos
2. **Full page captures**: Can be slow and large, use viewport if possible
3. **Batch operations**: Run multiple captures in parallel when possible
4. **OCR**: Slower than vision analysis, use only when exact text needed
5. **Browser captures**: Headless mode is faster than headed

## Next Steps

- Review the [README](../README.md) for installation and setup
- Check [plugin.json](../.claude-plugin/plugin.json) for configuration options
- Explore the [commands](../commands/) for detailed command documentation
- Try the [agents](../agents/) for specialized analysis
