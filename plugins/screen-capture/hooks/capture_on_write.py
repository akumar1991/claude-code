#!/usr/bin/env python3
"""
Capture on Write Hook
Captures screenshots after writing specific file types (e.g., UI files)
"""

import os
import sys
import json
from pathlib import Path
from fnmatch import fnmatch

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
    """Determine if we should capture based on file written"""

    # Check if enabled
    if not config.get("enabled", False):
        return False

    # Get file patterns to match
    file_patterns = config.get("file_patterns", [])
    if not file_patterns:
        return False

    # Get the file that was written
    tool_use = hook_input.get("tool_use", {})
    file_path = tool_use.get("parameters", {}).get("file_path", "")

    if not file_path:
        return False

    # Check if file matches any pattern
    filename = Path(file_path).name

    return any(fnmatch(filename, pattern) for pattern in file_patterns)


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

    # Get file that was written
    tool_use = hook_input.get("tool_use", {})
    file_path = tool_use.get("parameters", {}).get("file_path", "")

    # Create output directory
    output_dir = config.get("output_dir", "./write-screenshots")
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
            "timestamp": result["timestamp"],
            "trigger_file": file_path
        }

        # If analyze is enabled, note that
        if config.get("analyze", False):
            capture_result["note"] = f"Screenshot captured after writing {file_path}. Use /analyze-screenshot to review."

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
