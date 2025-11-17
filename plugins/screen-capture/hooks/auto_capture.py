#!/usr/bin/env python3
"""
Auto Capture Hook
Automatically captures screenshots on specific events (e.g., errors)
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent scripts directory to path
PLUGIN_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PLUGIN_DIR / "scripts"))

try:
    from screen_capture import ScreenCapture
except ImportError:
    print(json.dumps({
        "success": False,
        "error": "screen_capture module not found"
    }))
    sys.exit(1)


def should_capture(hook_input, config):
    """Determine if we should capture based on the hook input"""

    # Check if enabled
    if not config.get("enabled", False):
        return False

    # For error mode, check if command or output contains error indicators
    if config.get("mode") == "on-error":
        tool_use = hook_input.get("tool_use", {})
        tool_result = hook_input.get("tool_result", {})

        # Check command
        command = tool_use.get("parameters", {}).get("command", "")

        # Check output
        output = tool_result.get("output", "")
        error = tool_result.get("error", "")

        # Error indicators
        error_keywords = ["error", "fail", "exception", "traceback", "fatal", "crash"]

        combined_text = f"{command} {output} {error}".lower()

        return any(keyword in combined_text for keyword in error_keywords)

    return True


def main():
    # Read hook input from stdin
    try:
        hook_input = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        print(json.dumps({
            "success": False,
            "error": "Invalid JSON input"
        }))
        sys.exit(1)

    # Get configuration
    config = hook_input.get("config", {})

    # Check if we should capture
    if not should_capture(hook_input, config):
        # Don't capture, exit silently
        print(json.dumps({"success": True, "captured": False}))
        sys.exit(0)

    # Create output directory
    output_dir = config.get("output_dir", "./error-screenshots")
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Perform capture
    capturer = ScreenCapture(output_dir=output_dir)
    result = capturer.capture_screen(monitor=1)

    if result.get("success"):
        capture_result = {
            "success": True,
            "captured": True,
            "screenshot_path": result["path"],
            "dimensions": f"{result['width']}x{result['height']}",
            "timestamp": result["timestamp"]
        }

        # If analyze is enabled, note that
        if config.get("analyze", False):
            capture_result["note"] = "Screenshot captured. Use /analyze-screenshot to review."

        # If OCR is enabled
        if config.get("ocr", False):
            ocr_result = capturer.extract_text(result["path"])
            if ocr_result.get("success"):
                capture_result["ocr_text"] = ocr_result["text"]
                capture_result["word_count"] = ocr_result["word_count"]

        print(json.dumps(capture_result, indent=2))
    else:
        print(json.dumps({
            "success": False,
            "captured": False,
            "error": result.get("error", "Unknown error")
        }))
        sys.exit(1)


if __name__ == "__main__":
    main()
