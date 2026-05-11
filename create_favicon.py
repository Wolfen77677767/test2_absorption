#!/usr/bin/env python
# Script to create favicon files for the Gas Absorption Solver app

from PIL import Image, ImageDraw
import os
import sys

def create_favicons():
    """Create favicon files in PNG and ICO formats"""
    img_dir = os.path.join(os.path.dirname(__file__), 'static', 'images')
    
    # Create a professional favicon
    size = 256
    img = Image.new('RGBA', (size, size), (10, 14, 39, 255))  # Dark background
    draw = ImageDraw.Draw(img)
    
    # Draw blue circle (primary color: #0066FF)
    draw.ellipse([30, 30, 226, 226], fill=(0, 102, 255))
    
    # Draw cyan inner circle (secondary color: #00D9FF)
    draw.ellipse([50, 50, 206, 206], fill=(0, 217, 255))
    
    # Save PNG version
    png_path = os.path.join(img_dir, 'favicon.png')
    img.save(png_path, 'PNG')
    print(f'✓ Created: {png_path}')
    
    # Save ICO version with multiple sizes
    ico_path = os.path.join(img_dir, 'favicon.ico')
    sizes = [(16, 16), (32, 32), (64, 64), (128, 128)]
    ico_images = [img.resize(s, Image.Resampling.LANCZOS) for s in sizes]
    ico_images[0].save(ico_path, 'ICO', sizes=sizes)
    print(f'✓ Created: {ico_path}')
    
    print(f'\nFavicon files created successfully!')
    print(f'  - PNG: {png_path}')
    print(f'  - ICO: {ico_path}')
    return True

if __name__ == '__main__':
    try:
        create_favicons()
        sys.exit(0)
    except Exception as e:
        print(f'Error creating favicons: {e}', file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
