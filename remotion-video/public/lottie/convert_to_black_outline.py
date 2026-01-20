#!/usr/bin/env python3
"""Convert colored Lottie animations to black outline style - handles embedded images."""

import json
import copy
import base64
import io
from pathlib import Path
from PIL import Image


def is_color_array(val):
    """Check if value looks like a color array [r, g, b] or [r, g, b, a]."""
    if isinstance(val, list) and len(val) >= 3:
        return all(isinstance(v, (int, float)) and 0 <= v <= 1 for v in val[:3])
    return False


def convert_to_black(val):
    """Convert a color value to black."""
    if isinstance(val, list):
        if len(val) == 4:
            return [0, 0, 0, val[3]]
        elif len(val) == 3:
            return [0, 0, 0]
    return val


def deep_convert_colors(obj, to_black=True):
    """Recursively convert all colors in the object to black."""
    if isinstance(obj, dict):
        result = {}
        for key, val in obj.items():
            if key == 'sc' and isinstance(val, str):
                result[key] = '#000000' if to_black else '#FFFFFF'
            elif key == 'k':
                if isinstance(val, list):
                    if is_color_array(val):
                        result[key] = convert_to_black(val) if to_black else val
                    elif len(val) > 0 and isinstance(val[0], dict):
                        result[key] = []
                        for kf in val:
                            new_kf = dict(kf)
                            if 's' in new_kf and is_color_array(new_kf['s']):
                                new_kf['s'] = convert_to_black(new_kf['s']) if to_black else new_kf['s']
                            if 'e' in new_kf and is_color_array(new_kf['e']):
                                new_kf['e'] = convert_to_black(new_kf['e']) if to_black else new_kf['e']
                            result[key].append(new_kf)
                    else:
                        result[key] = deep_convert_colors(val, to_black)
                else:
                    result[key] = deep_convert_colors(val, to_black)
            else:
                result[key] = deep_convert_colors(val, to_black)
        return result
    elif isinstance(obj, list):
        return [deep_convert_colors(item, to_black) for item in obj]
    else:
        return obj


def convert_image_to_black_outline(base64_data: str) -> str:
    """Convert a base64 encoded image to black outline/silhouette."""
    # Remove data URL prefix if present
    if ',' in base64_data:
        header, data = base64_data.split(',', 1)
    else:
        header = 'data:image/png;base64'
        data = base64_data

    # Decode base64 to image
    img_data = base64.b64decode(data)
    img = Image.open(io.BytesIO(img_data))

    # Convert to RGBA if not already
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    # Get pixel data
    pixels = img.load()
    width, height = img.size

    # Convert to black silhouette (keep alpha, make all colors black)
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if a > 0:  # If pixel is visible
                # Convert to grayscale first
                gray = int(0.299 * r + 0.587 * g + 0.114 * b)
                # Threshold to black or white (for outline effect)
                if gray < 128:
                    pixels[x, y] = (0, 0, 0, a)  # Black
                else:
                    # For lighter areas, make them very dark gray for outline look
                    pixels[x, y] = (30, 30, 30, a)

    # Save back to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    new_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    return f"{header},{new_base64}"


def convert_assets_to_black(assets: list) -> list:
    """Convert all embedded images in assets to black outline."""
    converted_assets = []

    for asset in assets:
        new_asset = dict(asset)

        # Check if this is an embedded image (has 'p' with data URL or 'u' is empty)
        if 'p' in asset and (asset['p'].startswith('data:') or asset.get('u', '') == ''):
            if asset['p'].startswith('data:image'):
                print(f"    Converting embedded image: {asset.get('id', 'unknown')}")
                try:
                    new_asset['p'] = convert_image_to_black_outline(asset['p'])
                except Exception as e:
                    print(f"    Warning: Could not convert image {asset.get('id')}: {e}")

        converted_assets.append(new_asset)

    return converted_assets


def convert_lottie_to_black_outline(input_path, output_path=None):
    """Convert a Lottie JSON file to black outline style."""
    input_path = Path(input_path)

    if output_path is None:
        output_path = input_path.parent / f"{input_path.stem}-black{input_path.suffix}"
    else:
        output_path = Path(output_path)

    print(f"Converting: {input_path.name}")

    # Load the Lottie file
    with open(input_path, 'r') as f:
        lottie_data = json.load(f)

    # Make a deep copy
    converted = copy.deepcopy(lottie_data)

    # Convert vector colors
    converted = deep_convert_colors(converted, to_black=True)

    # Convert embedded images
    if 'assets' in converted:
        image_count = sum(1 for a in converted['assets'] if 'p' in a and a['p'].startswith('data:image'))
        if image_count > 0:
            print(f"  Found {image_count} embedded images")
            converted['assets'] = convert_assets_to_black(converted['assets'])

    # Save the converted file
    with open(output_path, 'w') as f:
        json.dump(converted, f, separators=(',', ':'))

    print(f"  -> {output_path.name}")
    return output_path


def main():
    """Convert all colored Lottie files in the current directory."""
    lottie_dir = Path(__file__).parent

    files_to_convert = [
        'stickman-talking.json',
        'stickman-walking.json',
        'thinking.json',
        'celebrating.json',
        'hello-wave.json',
    ]

    print("=" * 60)
    print("Converting Lottie animations to black outline style")
    print("=" * 60 + "\n")

    for filename in files_to_convert:
        input_path = lottie_dir / filename
        if input_path.exists():
            output_path = lottie_dir / f"{input_path.stem}-black.json"
            convert_lottie_to_black_outline(input_path, output_path)
            print()
        else:
            print(f"Skipped (not found): {filename}\n")

    print("=" * 60)
    print("Done! Black outline versions created with '-black' suffix.")
    print("=" * 60)


if __name__ == '__main__':
    main()
