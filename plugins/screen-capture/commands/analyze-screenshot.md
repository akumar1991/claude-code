---
description: Analyze screenshot or image with AI vision and OCR
hint: <image-path> [--ocr] [--detailed]
allowedTools:
  - Bash
  - Read
  - TodoWrite
---

# Analyze Screenshot Command

Analyzes screenshots and images using Claude's vision capabilities and optional OCR text extraction.

## Usage Examples

- `/analyze-screenshot ./screenshot.png` - Basic visual analysis
- `/analyze-screenshot ./screenshot.png --ocr` - Extract text using OCR
- `/analyze-screenshot ./screenshot.png --detailed` - Comprehensive analysis
- `/analyze-screenshot ./screenshot.png --ocr --lang fra` - OCR with French language

## Task Instructions

You are tasked with analyzing a screenshot or image file. Follow these steps:

1. **Parse Arguments**:
   - `image-path` (required): Path to the image file
   - `--ocr`: Perform OCR text extraction
   - `--detailed`: Provide detailed analysis
   - `--lang code`: OCR language code (default: eng)
   - `--focus aspect`: Focus analysis on specific aspect (ui, text, design, accessibility, errors)

2. **Validate Image**:
   - Check if file exists at the specified path
   - Verify file is an image (png, jpg, jpeg, gif, bmp, webp)
   - Check file size is reasonable (< 50MB)

3. **Read and Display Image**:
   - Use the Read tool to load the image
   - Claude can natively view images passed through the Read tool

4. **Perform Visual Analysis**:

   **Basic Analysis** (default):
   - Overall description of what's visible
   - Main elements and layout
   - Notable features or content
   - Purpose or context of the screenshot

   **Detailed Analysis** (if --detailed flag):
   - **Layout & Structure**: Grid, spacing, alignment, hierarchy
   - **UI Elements**: Buttons, forms, navigation, icons, typography
   - **Design Quality**: Color scheme, consistency, visual appeal
   - **Content**: Text, images, data visualizations, charts
   - **Functionality**: Apparent features and capabilities
   - **Accessibility**: Color contrast, text size, clarity
   - **Issues**: Bugs, errors, misalignments, broken elements
   - **Improvements**: Suggestions for enhancement

   **Focused Analysis** (if --focus specified):
   - **ui**: Focus on user interface elements, interactions, patterns
   - **text**: Focus on text content, readability, messaging
   - **design**: Focus on visual design, aesthetics, branding
   - **accessibility**: Focus on WCAG compliance, usability
   - **errors**: Focus on identifying bugs, issues, problems

5. **Optional: OCR Text Extraction** (if --ocr flag):
   - Run OCR using the screen_capture.py script:
     ```bash
     python3 /path/to/plugins/screen-capture/scripts/screen_capture.py ocr \
       -i [image-path] \
       --lang [lang-code] \
       --json
     ```
   - Parse the JSON result
   - Display:
     - Extracted text (full content)
     - Word count
     - Confident words count
     - Language detected
   - Analyze the extracted text for:
     - Key messages or information
     - Structure and organization
     - Potential data or patterns

6. **Combine Analysis** (if both vision and OCR):
   - Compare visual understanding with OCR text
   - Identify any discrepancies
   - Provide comprehensive insights combining both sources
   - Note any text that's difficult to read visually

7. **Generate Summary**:
   - Key findings (3-5 bullet points)
   - Primary purpose of the screenshot
   - Notable elements or issues
   - Recommended actions or insights

8. **Output Format**:
   ```
   📸 Screenshot Analysis: [filename]

   ## Visual Analysis
   [Description of what's visible]

   ## Key Elements
   - [Element 1]
   - [Element 2]
   - [Element 3]

   ## OCR Text Extraction (if requested)
   [Extracted text]
   Words: [count] | Confidence: [metrics]

   ## Insights
   [Key insights and findings]

   ## Recommendations
   [Suggested improvements or actions]
   ```

## Error Handling

- If image file doesn't exist, provide clear error message
- If image format is unsupported, list supported formats
- If OCR fails, explain potential causes (Tesseract not installed, poor image quality)
- If image is too large, suggest resizing or compression

## OCR Language Codes

Common language codes for `--lang` option:
- `eng` - English (default)
- `fra` - French
- `deu` - German
- `spa` - Spanish
- `ita` - Italian
- `por` - Portuguese
- `rus` - Russian
- `jpn` - Japanese
- `chi_sim` - Chinese Simplified
- `chi_tra` - Chinese Traditional

## Use Cases

- **UI Review**: Analyze application interfaces for usability
- **Error Investigation**: Examine error screenshots
- **Design Feedback**: Get design critique and suggestions
- **Documentation**: Extract text from screenshots for documentation
- **Accessibility Audit**: Check for accessibility issues
- **Bug Reports**: Analyze bug report screenshots
- **Competitive Analysis**: Examine competitor interfaces

## Notes

- Claude has native vision capabilities for detailed image analysis
- OCR is best for extracting specific text content
- Combined analysis provides the most comprehensive insights
- Image quality affects both vision analysis and OCR accuracy
- Large screenshots may need to be analyzed in sections
