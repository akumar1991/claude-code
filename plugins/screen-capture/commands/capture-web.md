---
description: Capture web page screenshot using browser automation
hint: <url> [--fullpage] [--element selector] [--extract]
allowedTools:
  - Bash
  - Read
  - Write
  - TodoWrite
---

# Web Page Capture Command

Captures screenshots of web pages using Puppeteer browser automation. Supports full page capture, specific element capture, and content extraction.

## Usage Examples

- `/capture-web https://example.com` - Capture full page screenshot
- `/capture-web https://example.com --viewport 1920x1080` - Custom viewport
- `/capture-web https://example.com --element "#main-content"` - Capture specific element
- `/capture-web https://example.com --extract` - Extract page content (HTML, text, links, images)
- `/capture-web https://example.com --wait-for "#load-indicator" --analyze` - Wait for element, then analyze

## Task Instructions

You are tasked with capturing a web page using browser automation. Follow these steps:

1. **Parse Arguments**:
   - `url` (required): The web page URL to capture
   - `--fullpage`: Capture entire page (default: true)
   - `--viewport WxH`: Viewport size (default: 1920x1080)
   - `--element selector`: Capture specific element by CSS selector
   - `--wait-for selector`: Wait for CSS selector before capturing
   - `--wait ms`: Additional wait time in milliseconds
   - `--format png|jpeg`: Output format (default: png)
   - `--no-javascript`: Disable JavaScript on the page
   - `--extract`: Extract page content instead of screenshot
   - `--analyze`: Analyze the captured screenshot
   - `--output path`: Custom output path

2. **Validate URL**:
   - Ensure URL is properly formatted
   - Add https:// if protocol is missing
   - Validate URL accessibility

3. **Create Output Directory**:
   - Ensure `./screenshots` directory exists
   - Use timestamped filenames

4. **Determine Capture Mode**:

   **A. Full Page Screenshot** (default):
   ```bash
   node /path/to/plugins/screen-capture/scripts/browser_capture.js page [url] \
     --width [width] --height [height] \
     --format [format] \
     --dir ./screenshots \
     --json
   ```

   **B. Element Capture** (if --element provided):
   ```bash
   node /path/to/plugins/screen-capture/scripts/browser_capture.js element [url] "[selector]" \
     --width [width] --height [height] \
     --format [format] \
     --dir ./screenshots \
     --json
   ```

   **C. Content Extraction** (if --extract flag):
   ```bash
   node /path/to/plugins/screen-capture/scripts/browser_capture.js extract [url] \
     --output ./screenshots/content_[timestamp].json \
     --json
   ```

5. **Handle Additional Options**:
   - If `--wait-for` is specified, add `--selector [selector]` to the command
   - If `--wait` is specified, add `--wait [ms]` to the command
   - If `--no-javascript` is specified, add `--no-javascript` flag
   - If `--output` is specified, add `--output [path]` to the command

6. **Execute Capture**:
   - Run the appropriate browser_capture.js command
   - Parse JSON output
   - Check for success/failure

7. **Display Results**:
   - Show success message with file path
   - Display page title and final URL
   - Show dimensions for screenshots
   - For extractions, show link count, image count, and text preview

8. **Optional: Analyze Screenshot** (if --analyze flag):
   - Use the Read tool to view the screenshot
   - Provide analysis of:
     - Page layout and design
     - UI/UX elements
     - Content hierarchy
     - Accessibility considerations
     - Visual issues or improvements
     - Text content and messaging

9. **Optional: Content Analysis** (if --extract was used):
   - Read the extracted JSON content
   - Summarize:
     - Page structure and main sections
     - Key links and navigation
     - Images and media
     - Important text content
     - Potential data extraction opportunities

## Error Handling

- If Node.js is not available, show installation instructions
- If Puppeteer is not installed: `npm install puppeteer` in plugin directory
- If URL is unreachable, provide clear error message
- If selector not found (element capture), suggest checking the selector
- Handle timeout errors gracefully

## Advanced Options

**Custom User Agent**:
```bash
--user-agent "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)"
```

**Quality for JPEG**:
```bash
--format jpeg --quality 85
```

**Wait for Dynamic Content**:
```bash
--wait-for ".dynamic-content" --wait 2000
```

## Notes

- Puppeteer runs in headless mode by default
- Screenshots include all content loaded via JavaScript
- Element capture automatically scrolls to the element
- Full page screenshots may be very large for long pages
- Extracted content includes rendered HTML and visible text
- Browser automation requires Node.js 18+ and sufficient memory
