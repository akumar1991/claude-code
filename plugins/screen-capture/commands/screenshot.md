---
description: Capture desktop screenshot with optional analysis
hint: [monitor] [--analyze] [--ocr]
allowedTools:
  - Bash
  - Read
  - Write
  - TodoWrite
---

# Desktop Screenshot Command

Captures a screenshot of your desktop screen and optionally analyzes it using Claude's vision capabilities.

## Usage Examples

- `/screenshot` - Capture primary monitor
- `/screenshot 2` - Capture monitor 2
- `/screenshot --analyze` - Capture and analyze the screenshot
- `/screenshot --ocr` - Capture and extract text via OCR
- `/screenshot --region 0 0 1920 1080` - Capture specific region

## Task Instructions

You are tasked with capturing a desktop screenshot. Follow these steps:

1. **Parse Arguments**:
   - Monitor number (default: 1)
   - `--analyze` flag: Whether to analyze the screenshot with vision
   - `--ocr` flag: Whether to extract text using OCR
   - `--region x y width height`: Capture specific region
   - `--output path`: Custom output path

2. **Create Screenshot Directory**:
   - Ensure `./screenshots` directory exists in the current working directory
   - Use timestamped filenames for organization

3. **Capture Screenshot**:
   - Use the screen_capture.py script from the plugin's scripts directory
   - Command format:
     ```bash
     python3 /path/to/plugins/screen-capture/scripts/screen_capture.py capture -m [monitor] -d ./screenshots --json
     ```
   - For region capture:
     ```bash
     python3 /path/to/plugins/screen-capture/scripts/screen_capture.py region -x [x] -y [y] -w [width] -h [height] -d ./screenshots --json
     ```

4. **Parse Result**:
   - The script outputs JSON with the capture result
   - Extract the `path` from the successful result
   - Display success message with file path and dimensions

5. **Optional: Analyze Screenshot** (if --analyze flag):
   - Use the Read tool to view the screenshot image
   - Provide detailed analysis of:
     - What's visible in the screenshot
     - UI elements and layout
     - Notable content or patterns
     - Potential improvements or issues
     - Any text visible in the image

6. **Optional: Extract Text** (if --ocr flag):
   - Use the OCR capability:
     ```bash
     python3 /path/to/plugins/screen-capture/scripts/screen_capture.py ocr -i [screenshot_path] --json
     ```
   - Display extracted text
   - Show word count and confidence metrics

7. **Summary**:
   - Display the screenshot path
   - Show dimensions
   - If analyzed, include key findings
   - If OCR performed, show text extraction summary

## Error Handling

- If Python dependencies are missing (mss, pillow, pytesseract), provide installation instructions
- If screenshot fails, suggest fallback methods based on platform
- Check if Tesseract OCR is installed for OCR functionality

## Notes

- Screenshots are saved with timestamps for easy organization
- The script supports cross-platform capture (macOS, Linux, Windows)
- OCR requires Tesseract to be installed on the system
- Vision analysis uses Claude's native image understanding capabilities
