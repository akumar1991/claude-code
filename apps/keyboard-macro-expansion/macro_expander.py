#!/usr/bin/env python3
"""
Keyboard Macro Expansion App

Press a single key (trigger) and it automatically types out a word or string.
Configure your macros in macros.json.

Usage:
    python macro_expander.py [--config path/to/macros.json]

Requirements:
    pip install pynput
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Callable

try:
    from pynput import keyboard
    from pynput.keyboard import Key, Controller
except ImportError:
    print("Error: pynput library not found.")
    print("Install it with: pip install pynput")
    sys.exit(1)


class MacroExpander:
    """Listens for trigger keys and expands them into configured text."""

    def __init__(self, macros: dict, trigger_prefix: str = None):
        """
        Initialize the macro expander.

        Args:
            macros: Dictionary mapping trigger keys to expansion text
            trigger_prefix: Optional prefix key (e.g., 'ctrl') that must be held
        """
        self.macros = macros
        self.trigger_prefix = trigger_prefix
        self.keyboard_controller = Controller()
        self.prefix_pressed = False
        self.listener = None
        self.running = False

    def _type_text(self, text: str, delay: float = 0.01):
        """Type out the text character by character."""
        for char in text:
            self.keyboard_controller.type(char)
            time.sleep(delay)

    def _on_press(self, key):
        """Handle key press events."""
        try:
            # Check for prefix key if configured
            if self.trigger_prefix:
                if hasattr(key, 'name') and key.name == self.trigger_prefix:
                    self.prefix_pressed = True
                    return

                # Only expand if prefix is held
                if not self.prefix_pressed:
                    return

            # Get the key character
            key_char = None
            if hasattr(key, 'char') and key.char:
                key_char = key.char
            elif hasattr(key, 'name'):
                key_char = key.name

            # Check if this key has a macro
            if key_char and key_char in self.macros:
                expansion = self.macros[key_char]

                # Small delay to let the trigger key register
                time.sleep(0.05)

                # Delete the trigger character (backspace)
                self.keyboard_controller.press(Key.backspace)
                self.keyboard_controller.release(Key.backspace)

                # Type the expansion
                self._type_text(expansion)

        except Exception as e:
            print(f"Error handling key press: {e}")

    def _on_release(self, key):
        """Handle key release events."""
        # Track prefix key release
        if self.trigger_prefix and hasattr(key, 'name'):
            if key.name == self.trigger_prefix:
                self.prefix_pressed = False

        # Check for exit key (Escape)
        if key == Key.esc:
            print("\nEscape pressed. Stopping macro expander...")
            self.stop()
            return False

    def start(self):
        """Start listening for keyboard events."""
        self.running = True
        print("Macro Expander is running!")
        print("Press ESC to exit.\n")
        print("Configured macros:")
        for trigger, expansion in self.macros.items():
            prefix_str = f"{self.trigger_prefix}+" if self.trigger_prefix else ""
            print(f"  {prefix_str}{trigger} -> {expansion}")
        print()

        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.listener.start()
        self.listener.join()

    def stop(self):
        """Stop the macro expander."""
        self.running = False
        if self.listener:
            self.listener.stop()


def load_macros(config_path: Path) -> tuple[dict, str | None]:
    """
    Load macros from a JSON configuration file.

    Returns:
        Tuple of (macros dict, trigger prefix or None)
    """
    if not config_path.exists():
        print(f"Config file not found: {config_path}")
        print("Creating default configuration...")
        create_default_config(config_path)

    with open(config_path, 'r') as f:
        config = json.load(f)

    macros = config.get('macros', {})
    trigger_prefix = config.get('trigger_prefix', None)

    return macros, trigger_prefix


def create_default_config(config_path: Path):
    """Create a default macros configuration file."""
    default_config = {
        "description": "Keyboard Macro Expansion Configuration",
        "trigger_prefix": None,
        "macros": {
            "1": "Hello, World!",
            "2": "Thank you for your email.",
            "3": "Best regards,",
            "4": "Please let me know if you have any questions.",
            "5": "I'll get back to you shortly."
        },
        "examples": {
            "with_prefix": {
                "description": "Set trigger_prefix to 'ctrl' to require Ctrl+key",
                "trigger_prefix": "ctrl",
                "macros": {
                    "e": "example@email.com",
                    "a": "123 Main Street, City, State 12345"
                }
            }
        }
    }

    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w') as f:
        json.dump(default_config, f, indent=2)

    print(f"Created default config at: {config_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Keyboard Macro Expansion - Press one key, type a phrase"
    )
    parser.add_argument(
        '--config', '-c',
        type=Path,
        default=Path(__file__).parent / 'macros.json',
        help='Path to macros configuration file (default: macros.json)'
    )
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List configured macros and exit'
    )

    args = parser.parse_args()

    # Load macros from config
    macros, trigger_prefix = load_macros(args.config)

    if not macros:
        print("No macros configured. Edit macros.json to add your macros.")
        sys.exit(1)

    if args.list:
        print("Configured macros:")
        for trigger, expansion in macros.items():
            prefix_str = f"{trigger_prefix}+" if trigger_prefix else ""
            print(f"  {prefix_str}{trigger} -> {expansion}")
        sys.exit(0)

    # Create and start the macro expander
    expander = MacroExpander(macros, trigger_prefix)

    try:
        expander.start()
    except KeyboardInterrupt:
        print("\nInterrupted. Stopping...")
        expander.stop()


if __name__ == '__main__':
    main()
