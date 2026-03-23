#!/usr/bin/env python3
"""
Static site generator for tagged image gallery (Booru-style)
- Individual pages for each image with full-size view and tags
- Tag pages showing all images with that tag
- Homepage with recent images
"""

import json
import os
from pathlib import Path
from datetime import datetime
from urllib.parse import quote
from jinja2 import Environment, FileSystemLoader

# Configuration
CONFIG = {
    'images_dir': 'images',
    'output_dir': 'docs',
    'template_dir': 'templates',
    'images_per_page': 20,
}

def extract_datetime_from_filename(filename):
    """
    Extract datetime from filename
    Formats supported:
    - YYYY-MM-DD (just date)
    - YYYY-MM-DD_HH-MM-SS (date and time)
    """
    base = Path(filename).stem
    
    # Try full datetime format first (YYYY-MM-DD_HH-MM-SS = 19 chars)
    if len(base) >= 19:
        datetime_str = base[:19]
        try:
            parts = datetime_str.split('_')
            if len(parts) == 2:
                date_part = parts[0]  # YYYY-MM-DD
                time_part = parts[1]  # HH-MM-SS
                
                datetime.strptime(date_part, '%Y-%m-%d')
                datetime.strptime(time_part, '%H-%M-%S')
                
                return datetime_str
        except ValueError:
            pass
    
    # Try date-only format (YYYY-MM-DD = 10 chars)
    if len(base) >= 10:
        datetime_str = base[:10]
        try:
            datetime.strptime(datetime_str, '%Y-%m-%d')
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
                tags = [tag.strip() for tag in content.split(',') if tag.strip()]
    except FileNotFoundError:
        pass
    return tags

def url_encode_tag(tag):
    """URL encode tag name for safe file paths"""
    return quote(tag.replace(' ', '_').lower(), safe='')

def load_image_metadata():
    """Load metadata from image filenames and .txt files"""
    images = []
    images_path = Path(CONFIG['images_dir'])
    
    img_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
    
    for img_file in sorted(images_path.iterdir(), reverse=True):  # Newest first
        if img_file.suffix.lower() in img_extensions:
            filename = img_file.name
            
            datetime_str = extract_datetime_from_filename(filename)
            
            if not datetime_str:
                print(f"⚠️  Skipping {filename} - filename doesn't start with YYYY-MM-DD or YYYY-MM-DD_HH-MM-SS format")
                continue
            
            txt_file = img_file.with_suffix('.txt')
            tags = load_tags_from_txt(txt_file)
            
            # Create slug for URL (filename without extension)
            slug = Path(filename).stem
            
            metadata = {
                'filename': filename,
                'slug': slug,
                'date_added': datetime_str,
                'tags': tags
            }
            
            images.append(metadata)
            print(f"✅ Loaded {filename} | Date: {datetime_str} | Tags: {', '.join(tags) if tags else 'None'}")
    
    return images

def get_all_tags(images):
    """Extract all unique tags and count occurrences"""
    tag_count = {}
    for img in images:
        for tag in img.get('tags', []):
            tag_count[tag] = tag_count.get(tag, 0) + 1
    
    return sorted(tag_count.items())

def generate_image_page(env, image, all_images, all_tags_dict):
    """Generate individual image page"""
    template = env.get_template('image.html')
    
    # Find previous and next images
    image_index = next(i for i, img in enumerate(all_images) if img['slug'] == image['slug'])
    prev_image = all_images[image_index + 1] if image_index + 1 < len(all_images) else None
    next_image = all_images[image_index - 1] if image_index > 0 else None
    
    html = template.render(
        image=image,
        prev_image=prev_image,
        next_image=next_image,
        all_tags=all_tags_dict
    )
    
    # Create image page directory
    image_dir = Path(CONFIG['output_dir']) / 'images'
    image_dir.mkdir(exist_ok=True)
    
    output_file = image_dir / f"{image['slug']}.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

def generate_tag_page(env, tag, tagged_images):
    """Generate tag gallery page"""
    template = env.get_template('tag.html')
    
    html = template.render(
        tag=tag,
        images=tagged_images,
        count=len(tagged_images)
    )
    
    # Create tag page directory
    tag_dir = Path(CONFIG['output_dir']) / 'tags'
    tag_dir.mkdir(exist_ok=True)
    
    # URL encode tag for safe filename
    tag_slug = url_encode_tag(tag)
    output_file = tag_dir / f"{tag_slug}.html"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

def generate_homepage(env, images):
    """Generate homepage with recent images"""
    template = env.get_template('index.html')
    
    html = template.render(
        images=images[:CONFIG['images_per_page']],  # Show recent images
        total_images=len(images)
    )
    
    output_file = Path(CONFIG['output_dir']) / 'index.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

def generate_site():
    """Generate entire static site"""
    os.makedirs(CONFIG['output_dir'], exist_ok=True)
    
    # Load metadata
    images = load_image_metadata()
    all_tags_list = get_all_tags(images)
    all_tags_dict = {tag: count for tag, count in all_tags_list}
    
    if not images:
        print("❌ No images found with valid filenames (YYYY-MM-DD or YYYY-MM-DD_HH-MM-SS format)")
        return
    
    # Setup Jinja2
    env = Environment(loader=FileSystemLoader(CONFIG['template_dir']))
    # Register url_encode_tag as a global function in Jinja2
    env.globals['url_encode_tag'] = url_encode_tag
    
    # Generate homepage
    print("\n📄 Generating homepage...")
    generate_homepage(env, images)
    
    # Generate individual image pages
    print("📄 Generating image pages...")
    for image in images:
        generate_image_page(env, image, images, all_tags_dict)
    
    # Generate tag pages
    print("📄 Generating tag pages...")
    for tag, count in all_tags_list:
        tagged_images = [img for img in images if tag in img['tags']]
        generate_tag_page(env, tag, tagged_images)
    
    print(f"\n✅ Generated gallery!")
    print(f"   📸 {len(images)} image pages")
    print(f"   🏷️  {len(all_tags_list)} tag pages")
    print(f"   📁 Output saved to {CONFIG['output_dir']}/")

if __name__ == '__main__':
    generate_site()