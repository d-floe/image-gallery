#!/usr/bin/env python3
"""
Static site generator for tagged image gallery
Tags: Read from .txt files with same name as image
Date: Extracted from first 19 characters of filename (YYYY-MM-DD_HH-MM-SS)
"""

import json
import os
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

# Configuration
CONFIG = {
    'images_dir': 'images',
    'output_dir': 'docs',
    'template_dir': 'templates',
}

def extract_datetime_from_filename(filename):
    """
    Extract datetime from first 19 characters of filename
    Format: YYYY-MM-DD_HH-MM-SS
    Example: 2026-03-23_14-30-45_my-photo.jpg -> 2026-03-23_14-30-45
    """
    # Remove extension and get base name
    base = Path(filename).stem
    
    # Extract first 19 characters
    if len(base) >= 19:
        datetime_str = base[:19]
        # Validate format: YYYY-MM-DD_HH-MM-SS
        try:
            # Replace underscores and dashes to parse
            normalized = datetime_str.replace('_', '-').replace('-', ' ', 2)  # Keep date dashes, convert time dashes
            # Actually, let's just validate the pattern
            parts = datetime_str.split('_')
            if len(parts) == 2:
                date_part = parts[0]  # YYYY-MM-DD
                time_part = parts[1]  # HH-MM-SS
                
                # Validate date format
                datetime.strptime(date_part, '%Y-%m-%d')
                # Validate time format
                datetime.strptime(time_part, '%H-%M-%S')
                
                return datetime_str
        except ValueError:
            pass
    
    return None

def load_tags_from_txt(txt_file):
    """Load tags from a .txt file"""
    tags = []
    try:
        with open(txt_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                # Split by comma and strip whitespace
                tags = [tag.strip() for tag in content.split(',') if tag.strip()]
    except FileNotFoundError:
        pass
    return tags

def load_image_metadata():
    """Load metadata from image filenames and .txt files"""
    images = []
    images_path = Path(CONFIG['images_dir'])
    
    # Supported image extensions
    img_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
    
    # Find all image files
    for img_file in sorted(images_path.iterdir()):
        if img_file.suffix.lower() in img_extensions:
            filename = img_file.name
            
            # Extract datetime from filename
            datetime_str = extract_datetime_from_filename(filename)
            
            if not datetime_str:
                print(f"⚠️  Skipping {filename} - filename doesn't start with YYYY-MM-DD_HH-MM-SS format")
                continue
            
            # Load tags from corresponding .txt file
            txt_file = img_file.with_suffix('.txt')
            tags = load_tags_from_txt(txt_file)
            
            # Create image metadata
            metadata = {
                'filename': filename,
                'date_added': datetime_str,
                'tags': tags
            }
            
            images.append(metadata)
            print(f"✅ Loaded {filename} | Date: {datetime_str} | Tags: {', '.join(tags) if tags else 'None'}")
    
    return images

def get_all_tags(images):
    """Extract all unique tags from images"""
    tags = set()
    for img in images:
        tags.update(img.get('tags', []))
    return sorted(list(tags))

def generate_site():
    """Generate static HTML site"""
    # Create output directory
    os.makedirs(CONFIG['output_dir'], exist_ok=True)
    
    # Load metadata
    images = load_image_metadata()
    all_tags = get_all_tags(images)
    
    if not images:
        print("❌ No images found with valid filenames (YYYY-MM-DD_HH-MM-SS format)")
        return
    
    # Setup Jinja2
    env = Environment(loader=FileSystemLoader(CONFIG['template_dir']))
    
    # Generate index page
    template = env.get_template('index.html')
    html = template.render(
        images=images,
        all_tags=all_tags,
        total_images=len(images)
    )
    
    with open(os.path.join(CONFIG['output_dir'], 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n✅ Generated gallery with {len(images)} images")
    print(f"📝 Found {len(all_tags)} unique tags")
    print(f"📁 Output saved to {CONFIG['output_dir']}/")

if __name__ == '__main__':
    generate_site()