# Keyboard Macro Expansion App

Press a single key and it automatically types out a word or string of letters.

## Quick Start

1. **Install the dependency:**
   ```bash
   pip install pynput
   ```

2. **Run the app:**
   ```bash
   python macro_expander.py
   ```

3. **Press a trigger key (1-9 by default) and watch it expand!**

4. **Press ESC to exit.**

## How It Works

When the app is running, pressing a configured trigger key will:
1. Delete the trigger character you just typed
2. Type out the full expansion text in its place

## Configuration

Edit `macros.json` to customize your macros:

```json
{
  "trigger_prefix": null,
  "macros": {
    "1": "Hello, World!",
    "2": "Thank you for your email.",
    "e": "myemail@example.com"
  }
}
```

### Configuration Options

| Option | Description | Example |
|--------|-------------|---------|
| `trigger_prefix` | Optional modifier key required | `"ctrl"`, `"alt"`, `"shift"`, or `null` |
| `macros` | Key-value pairs of trigger -> expansion | `{"1": "Hello!"}` |

### Using a Trigger Prefix

To avoid accidental expansions, you can require a modifier key to be held:

```json
{
  "trigger_prefix": "ctrl",
  "macros": {
    "e": "myemail@example.com",
    "a": "123 Main Street, City, State 12345"
  }
}
```

Now you need to press **Ctrl+e** to expand to your email.

## Command Line Options

```bash
# Use default macros.json in the same directory
python macro_expander.py

# Use a custom config file
python macro_expander.py --config /path/to/my-macros.json

# List configured macros without running
python macro_expander.py --list
```

## Example Use Cases

### Email Templates
```json
{
  "macros": {
    "1": "Thank you for reaching out. I'll review your request and get back to you within 24 hours.",
    "2": "Please find the requested information attached to this email.",
    "3": "Best regards,\nYour Name\nYour Title"
  }
}
```

### Code Snippets
```json
{
  "trigger_prefix": "alt",
  "macros": {
    "c": "console.log();",
    "f": "function () {\n  \n}",
    "l": "for (let i = 0; i < arr.length; i++) {\n  \n}"
  }
}
```

### Contact Information
```json
{
  "trigger_prefix": "ctrl",
  "macros": {
    "e": "john.doe@company.com",
    "p": "+1 (555) 123-4567",
    "a": "123 Business Ave, Suite 100, City, State 12345"
  }
}
```

## Platform Notes

- **Linux**: May require running with `sudo` or adding your user to the `input` group
- **macOS**: Grant accessibility permissions in System Preferences > Security & Privacy > Privacy > Accessibility
- **Windows**: Should work out of the box

## Troubleshooting

**"Permission denied" on Linux:**
```bash
sudo python macro_expander.py
# Or add yourself to the input group:
sudo usermod -aG input $USER
# Then log out and back in
```

**"pynput not found":**
```bash
pip install pynput
```

**Macros not working in certain applications:**
Some applications (especially those with elevated privileges) may not receive simulated keystrokes. Try running the macro expander with elevated privileges.

## License

MIT License
