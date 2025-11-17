#!/usr/bin/env python3
"""
Comprehensive Screen Capture Tool
Supports desktop, window, and region capture across platforms
"""

import os
import sys
import json
import argparse
import platform
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

try:
    from mss import mss
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


class ScreenCapture:
    """Cross-platform screen capture utility"""

    def __init__(self, output_dir: str = "./screenshots"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.platform = platform.system()

    def _generate_filename(self, prefix: str = "screenshot", extension: str = "png") -> str:
        """Generate timestamped filename"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}.{extension}"

    def capture_screen(self, monitor: int = 0, output_path: Optional[str] = None) -> Dict:
        """
        Capture full screen or specific monitor

        Args:
            monitor: Monitor number (0 = all monitors, 1+ = specific monitor)
            output_path: Custom output path (optional)

        Returns:
            Dict with capture metadata
        """
        if not MSS_AVAILABLE:
            return self._fallback_capture(output_path)

        if output_path is None:
            output_path = self.output_dir / self._generate_filename("fullscreen")
        else:
            output_path = Path(output_path)

        try:
            with mss() as sct:
                # Get monitor info
                if monitor == 0:
                    # Capture all monitors as one
                    monitor_data = sct.monitors[0]
                else:
                    # Capture specific monitor
                    monitor_data = sct.monitors[min(monitor, len(sct.monitors) - 1)]

                # Capture screenshot
                screenshot = sct.grab(monitor_data)

                # Save to file
                mss.tools.to_png(screenshot.rgb, screenshot.size, output=str(output_path))

                return {
                    "success": True,
                    "path": str(output_path.absolute()),
                    "width": screenshot.width,
                    "height": screenshot.height,
                    "monitor": monitor,
                    "timestamp": datetime.now().isoformat(),
                    "method": "mss"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "method": "mss"
            }

    def _fallback_capture(self, output_path: Optional[str] = None) -> Dict:
        """Fallback to platform-specific tools when mss is unavailable"""
        if output_path is None:
            output_path = self.output_dir / self._generate_filename("fullscreen")
        else:
            output_path = Path(output_path)

        try:
            if self.platform == "Darwin":  # macOS
                os.system(f'screencapture -x "{output_path}"')
            elif self.platform == "Linux":
                os.system(f'scrot "{output_path}" 2>/dev/null || '
                         f'gnome-screenshot -f "{output_path}" 2>/dev/null || '
                         f'import -window root "{output_path}"')
            elif self.platform == "Windows":
                # Use PowerShell for Windows
                ps_script = f'''
                Add-Type -AssemblyName System.Windows.Forms
                Add-Type -AssemblyName System.Drawing
                $screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
                $bitmap = New-Object System.Drawing.Bitmap $screen.Width, $screen.Height
                $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
                $graphics.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size)
                $bitmap.Save("{output_path}")
                $graphics.Dispose()
                $bitmap.Dispose()
                '''
                os.system(f'powershell -Command "{ps_script}"')

            # Check if file was created
            if output_path.exists():
                # Get image dimensions
                if PIL_AVAILABLE:
                    img = Image.open(output_path)
                    width, height = img.size
                    img.close()
                else:
                    width, height = 0, 0

                return {
                    "success": True,
                    "path": str(output_path.absolute()),
                    "width": width,
                    "height": height,
                    "timestamp": datetime.now().isoformat(),
                    "method": "system_command"
                }
            else:
                return {
                    "success": False,
                    "error": "Screenshot file not created",
                    "method": "system_command"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "method": "system_command"
            }

    def capture_region(self, x: int, y: int, width: int, height: int,
                      output_path: Optional[str] = None) -> Dict:
        """
        Capture specific screen region

        Args:
            x, y: Top-left corner coordinates
            width, height: Region dimensions
            output_path: Custom output path (optional)
        """
        if output_path is None:
            output_path = self.output_dir / self._generate_filename("region")
        else:
            output_path = Path(output_path)

        if not MSS_AVAILABLE:
            return {
                "success": False,
                "error": "mss library required for region capture. Install with: pip install mss"
            }

        try:
            with mss() as sct:
                monitor = {"top": y, "left": x, "width": width, "height": height}
                screenshot = sct.grab(monitor)
                mss.tools.to_png(screenshot.rgb, screenshot.size, output=str(output_path))

                return {
                    "success": True,
                    "path": str(output_path.absolute()),
                    "width": width,
                    "height": height,
                    "region": {"x": x, "y": y, "width": width, "height": height},
                    "timestamp": datetime.now().isoformat(),
                    "method": "mss"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def extract_text(self, image_path: str, lang: str = "eng") -> Dict:
        """
        Extract text from image using OCR

        Args:
            image_path: Path to image file
            lang: OCR language (default: eng)
        """
        if not TESSERACT_AVAILABLE:
            return {
                "success": False,
                "error": "pytesseract not installed. Install with: pip install pytesseract"
            }

        if not PIL_AVAILABLE:
            return {
                "success": False,
                "error": "Pillow not installed. Install with: pip install pillow"
            }

        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, lang=lang)

            # Also get detailed data
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, lang=lang)

            # Count words with confidence > 60
            confident_words = sum(1 for conf in data['conf'] if int(conf) > 60)

            image.close()

            return {
                "success": True,
                "text": text.strip(),
                "word_count": len(text.split()),
                "confident_words": confident_words,
                "language": lang,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def list_monitors(self) -> Dict:
        """List available monitors"""
        if not MSS_AVAILABLE:
            return {
                "success": False,
                "error": "mss library required. Install with: pip install mss"
            }

        try:
            with mss() as sct:
                monitors = []
                for i, monitor in enumerate(sct.monitors):
                    monitors.append({
                        "id": i,
                        "width": monitor["width"],
                        "height": monitor["height"],
                        "left": monitor.get("left", 0),
                        "top": monitor.get("top", 0)
                    })

                return {
                    "success": True,
                    "monitors": monitors,
                    "count": len(monitors)
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


def main():
    parser = argparse.ArgumentParser(description="Cross-platform screen capture tool")
    parser.add_argument("action", choices=["capture", "region", "ocr", "list-monitors"],
                       help="Action to perform")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("-m", "--monitor", type=int, default=1,
                       help="Monitor number (default: 1)")
    parser.add_argument("-x", type=int, help="Region X coordinate")
    parser.add_argument("-y", type=int, help="Region Y coordinate")
    parser.add_argument("-w", "--width", type=int, help="Region width")
    parser.add_argument("-h", "--height", type=int, help="Region height", dest="height")
    parser.add_argument("-i", "--image", help="Image path for OCR")
    parser.add_argument("-l", "--lang", default="eng", help="OCR language (default: eng)")
    parser.add_argument("-d", "--dir", default="./screenshots",
                       help="Output directory (default: ./screenshots)")
    parser.add_argument("--json", action="store_true",
                       help="Output result as JSON")

    args = parser.parse_args()

    capturer = ScreenCapture(output_dir=args.dir)
    result = {}

    if args.action == "capture":
        result = capturer.capture_screen(monitor=args.monitor, output_path=args.output)

    elif args.action == "region":
        if not all([args.x is not None, args.y is not None,
                   args.width is not None, args.height is not None]):
            print("Error: Region capture requires -x, -y, -w, -h arguments", file=sys.stderr)
            sys.exit(1)
        result = capturer.capture_region(args.x, args.y, args.width, args.height,
                                        output_path=args.output)

    elif args.action == "ocr":
        if not args.image:
            print("Error: OCR requires -i/--image argument", file=sys.stderr)
            sys.exit(1)
        result = capturer.extract_text(args.image, lang=args.lang)

    elif args.action == "list-monitors":
        result = capturer.list_monitors()

    # Output result
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result.get("success"):
            if args.action in ["capture", "region"]:
                print(f"✓ Screenshot saved to: {result['path']}")
                print(f"  Dimensions: {result['width']}x{result['height']}")
            elif args.action == "ocr":
                print(f"✓ Text extracted ({result['word_count']} words):")
                print(result['text'])
            elif args.action == "list-monitors":
                print(f"✓ Found {result['count']} monitor(s):")
                for mon in result['monitors']:
                    print(f"  Monitor {mon['id']}: {mon['width']}x{mon['height']} "
                          f"at ({mon['left']}, {mon['top']})")
        else:
            print(f"✗ Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
