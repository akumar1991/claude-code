#!/usr/bin/env python3
"""
Periodic Capture Hook
Captures screenshots at regular intervals during development sessions
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

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


STATE_FILE = Path.home() / ".claude-code" / "screen-capture-state.json"


def load_state():
    """Load capture state from file"""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        "last_capture": None,
        "session_captures": 0,
        "session_start": datetime.now().isoformat()
    }


def save_state(state):
    """Save capture state to file"""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def should_capture(state, config):
    """Determine if enough time has passed for next capture"""

    # Check if enabled
    if not config.get("enabled", False):
        return False

    # Check max captures per session
    max_captures = config.get("max_captures_per_session", 20)
    if state["session_captures"] >= max_captures:
        return False

    # Check time interval
    interval_minutes = config.get("interval_minutes", 5)

    if state["last_capture"] is None:
        return True

    last_capture_time = datetime.fromisoformat(state["last_capture"])
    now = datetime.now()
    elapsed = now - last_capture_time

    return elapsed >= timedelta(minutes=interval_minutes)


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

    # Load state
    state = load_state()

    # Check if we should capture
    if not should_capture(state, config):
        # Don't capture, exit silently
        print(json.dumps({"success": True, "captured": False}))
        sys.exit(0)

    # Create output directory
    output_dir = config.get("output_dir", "./session-screenshots")
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Perform capture
    capturer = ScreenCapture(output_dir=output_dir)
    result = capturer.capture_screen(monitor=1)

    if result.get("success"):
        # Update state
        state["last_capture"] = datetime.now().isoformat()
        state["session_captures"] += 1
        save_state(state)

        capture_result = {
            "success": True,
            "captured": True,
            "screenshot_path": result["path"],
            "dimensions": f"{result['width']}x{result['height']}",
            "timestamp": result["timestamp"],
            "session_capture_number": state["session_captures"]
        }

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
