#!/usr/bin/env python3
"""
Static site generator for tagged image gallery (Booru-style)
- Individual pages for each image with full-size view and tags
- Tag pages showing all images with that tag
- Homepage with recent images
- Auto-generates thumbnails for faster loading
- Pagination for gallery views
- Cleanup of orphaned files
"""

import json
import math
import os
import re
from pathlib import Path
from datetime import datetime
from PIL import Image
from jinja2 import Environment, FileSystemLoader

# Configuration
CONFIG = {
    'images_dir': 'docs/images',
    'output_dir': 'docs',
    'template_dir': 'templates',
    'images_per_page': 50,
    'thumbnail_size': (300, 300),  # Width x Height for thumbnails
    'thumbnail_dir': 'thumbnails',  # Subdirectory in docs for thumbnails
}

# Character mappings for special characters
CHAR_MAPPINGS = {
    ':': 'COL',
    '^': 'CRT',
    '=': 'EQL',
    '!': 'EXL',
    '?': 'QST',
    '#': 'HSH',
    '@': 'AT',
    '$': 'DLR',
    '%': 'PCT',
    '&': 'AMP',
    '*': 'AST',
    '+': 'PLS',
    '~': 'TLD',
    '`': 'BCK',
    '|': 'PIP',
    '\\': 'BSH',
    '/': 'SLS',
    '<': 'LT',
    '>': 'GT',
    '"': 'QT',
    "'": 'APO',
    '[': 'LBR',
    ']': 'RBR',
    '{': 'LCB',
    '}': 'RCB',
    ',': 'COM',
    '.': 'DOT',
    ';': 'SMC',
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

def tag_to_slug(tag):
    """Convert tag name to slug using character mappings"""
    slug = tag.replace(' ', '_').lower()
    
    # Replace special characters with their mappings
    for char, replacement in CHAR_MAPPINGS.items():
        slug = slug.replace(char, replacement)
    
    return slug

def generate_thumbnail(image_path, thumbnail_path, size=CONFIG['thumbnail_size']):
    """Generate a thumbnail for the image, preserving format compatibility"""
    try:
        img = Image.open(image_path)
        
        # Convert RGBA to RGB if saving as JPEG
        if img.mode == 'RGBA':
            # Create white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
            img = background
        elif img.mode not in ('RGB', 'L'):
            # Convert other modes to RGB
            img = img.convert('RGB')
        
        img.thumbnail(size, Image.Resampling.LANCZOS)
        img.save(thumbnail_path, quality=85, optimize=True)
        return True
    except Exception as e:
        print(f"⚠️  Failed to generate thumbnail for {image_path}: {e}")
        return False

def load_image_metadata():
    """Load metadata from image filenames and .txt files"""
    images = []
    images_path = Path(CONFIG['images_dir'])
    
    img_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
    
    # Create thumbnails directory
    thumbnail_dir = Path(CONFIG['output_dir']) / CONFIG['thumbnail_dir']
    thumbnail_dir.mkdir(parents=True, exist_ok=True)
    
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
            
            # Generate thumbnail
            thumb_filename = f"{slug}.jpg"
            thumb_path = thumbnail_dir / thumb_filename
            generate_thumbnail(str(img_file), str(thumb_path), CONFIG['thumbnail_size'])
            
            metadata = {
                'filename': filename,
                'slug': slug,
                'thumbnail': thumb_filename,
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

def load_tag_categories():
    """Load tag categories and colors from config file"""
    tag_to_category = {}
    category_colors = {}
    config_file = Path('tags_config.json')
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            for category, data in config.get('tag_categories', {}).items():
                color = data.get('color', '#58a6ff')
                category_colors[category] = color
                for tag in data.get('tags', []):
                    tag_to_category[tag] = category
        print(f"✅ Loaded {len(tag_to_category)} tag category mappings from tags_config.json")
    except FileNotFoundError:
        print("⚠️  tags_config.json not found - using default colors for all tags")
    except json.JSONDecodeError:
        print("⚠️  Error parsing tags_config.json - using default colors for all tags")
    
    return tag_to_category, category_colors

def generate_tag_css(category_colors):
    """Generate CSS for tag colors based on categories"""
    css_content = "/* Auto-generated tag color styles */\n\n"
    
    if not category_colors:
        css_content += "/* No tag categories found - using default colors */\n"
    else:
        for category, color in category_colors.items():
            category_slug = tag_to_slug(category)
            css_content += f".tag-category-{category_slug} {{\n"
            css_content += f"    background-color: {color} !important;\n"
            css_content += f"}}\n\n"
    
    # Write to CSS file
    css_file = Path(CONFIG['output_dir']) / 'tags_colors.css'
    with open(css_file, 'w', encoding='utf-8') as f:
        f.write(css_content)
    
    print(f"✅ Generated tags_colors.css ({len(category_colors)} categories)")
    return css_file

def cleanup_orphaned_files(images, all_tags_list):
    """Remove HTML pages and thumbnails that are no longer needed"""
    output_dir = Path(CONFIG['output_dir'])
    
    # Track files that should exist
    valid_files = set()
    
    # Add homepage pages
    items_per_page = CONFIG['images_per_page']
    total_pages = math.ceil(len(images) / items_per_page)
    for page_num in range(1, total_pages + 1):
        if page_num == 1:
            valid_files.add('index.html')
        else:
            valid_files.add(f'page_{page_num}.html')
    
    # Add image pages
    for image in images:
        valid_files.add(f'images/{image["slug"]}.html')
    
    # Add tag pages
    for tag, _ in all_tags_list:
        tag_slug = tag_to_slug(tag)
        tagged_count = sum(1 for img in images if tag in img['tags'])
        tag_pages = math.ceil(tagged_count / items_per_page)
        
        for page_num in range(1, tag_pages + 1):
            if page_num == 1:
                valid_files.add(f'tags/{tag_slug}.html')
            else:
                valid_files.add(f'tags/{tag_slug}_page_{page_num}.html')
    
    # Add valid thumbnails
    valid_thumbnails = set()
    for image in images:
        valid_thumbnails.add(image['thumbnail'])
    
    # Remove orphaned HTML files
    images_dir = output_dir / 'images'
    if images_dir.exists():
        for html_file in images_dir.glob('*.html'):
            if html_file.name not in [f.split('/')[-1] for f in valid_files if f.startswith('images/')]:
                print(f"🗑️  Removing orphaned image page: {html_file.name}")
                html_file.unlink()
    
    tags_dir = output_dir / 'tags'
    if tags_dir.exists():
        for html_file in tags_dir.glob('*.html'):
            if html_file.name not in [f.split('/')[-1] for f in valid_files if f.startswith('tags/')]:
                print(f"🗑️  Removing orphaned tag page: {html_file.name}")
                html_file.unlink()
    
    # Remove orphaned homepage pages
    for html_file in output_dir.glob('page_*.html'):
        if html_file.name not in valid_files:
            print(f"🗑️  Removing orphaned homepage page: {html_file.name}")
            html_file.unlink()
    
    # Remove orphaned thumbnails
    thumbnail_dir = output_dir / CONFIG['thumbnail_dir']
    if thumbnail_dir.exists():
        for thumb_file in thumbnail_dir.glob('*.jpg'):
            if thumb_file.name not in valid_thumbnails:
                print(f"🗑️  Removing orphaned thumbnail: {thumb_file.name}")
                thumb_file.unlink()

def generate_title(image, tag_to_category):
    """Generate a human-readable title from character and artist tags.

    Format: "<Character1> and <Character2> by <artist>"
    Falls back to the image slug if no relevant tags are found.

    Args:
        image (dict): Image metadata dict containing 'tags' and 'slug' keys.
        tag_to_category (dict): Mapping of tag name to category string.

    Returns:
        str: Formatted title string, e.g. "Ash Sarai and Sumi Ezaki by d-floe".
    """
    character_tags = [t for t in image.get('tags', []) if tag_to_category.get(t) == 'character']
    artist_tags = [t for t in image.get('tags', []) if tag_to_category.get(t) == 'artist']

    if not character_tags and not artist_tags:
        return image['slug']

    def format_character(tag):
        # Remove trailing _(anything) suffix, e.g. ash_sarai_(d-floe) -> ash_sarai
        name = re.sub(r'_\([^)]*\)$', '', tag)
        # Replace underscores with spaces and title-case
        return name.replace('_', ' ').title()

    parts = []
    if character_tags:
        char_names = [format_character(t) for t in character_tags]
        parts.append(' and '.join(char_names))

    if artist_tags:
        parts.append('by ' + artist_tags[0])

    return ' '.join(parts) if parts else image['slug']


def generate_image_page(env, image, all_images, all_tags_dict, tag_to_category):
    """Generate individual image page"""
    template = env.get_template('item.html')
    
    # Find previous and next images
    image_index = next(i for i, img in enumerate(all_images) if img['slug'] == image['slug'])
    prev_image = all_images[image_index + 1] if image_index + 1 < len(all_images) else None
    next_image = all_images[image_index - 1] if image_index > 0 else None
    
    # Add category information to tags
    tags_with_category = []
    for tag in image.get('tags', []):
        tags_with_category.append({
            'name': tag,
            'category': tag_to_category.get(tag, 'default')
        })
    
    # Sort tags by category order: artist, character, meta, then default
    category_order = {'artist': 0, 'character': 1, 'meta': 2, 'default': 3}
    tags_with_category.sort(key=lambda x: (category_order.get(x['category'], 999), x['name']))
    
    image_title = generate_title(image, tag_to_category)

    html = template.render(
        image=image,
        image_title=image_title,
        prev_image=prev_image,
        next_image=next_image,
        all_tags=all_tags_dict,
        tags_with_category=tags_with_category
    )
    
    # Create image page directory
    image_dir = Path(CONFIG['output_dir']) / 'items'
    image_dir.mkdir(exist_ok=True)
    
    output_file = image_dir / f"{image['slug']}.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

def generate_tag_pages(env, tag, tagged_images):
    """Generate paginated tag gallery pages"""
    items_per_page = CONFIG['images_per_page']
    total_pages = math.ceil(len(tagged_images) / items_per_page)
    
    template = env.get_template('tag.html')
    
    # Create tag page directory
    tag_dir = Path(CONFIG['output_dir']) / 'tags'
    tag_dir.mkdir(exist_ok=True)
    
    tag_slug = tag_to_slug(tag)
    
    for page_num in range(1, total_pages + 1):
        start_idx = (page_num - 1) * items_per_page
        end_idx = start_idx + items_per_page
        page_images = tagged_images[start_idx:end_idx]
        
        html = template.render(
            tag=tag,
            images=page_images,
            count=len(tagged_images),
            current_page=page_num,
            total_pages=total_pages,
            tag_slug=tag_slug
        )
        
        # First page is index.html, others are page_2.html, page_3.html, etc.
        if page_num == 1:
            output_file = tag_dir / f"{tag_slug}.html"
        else:
            output_file = tag_dir / f"{tag_slug}_page_{page_num}.html"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

def generate_homepage_pages(env, images):
    """Generate paginated homepage"""
    items_per_page = CONFIG['images_per_page']
    total_pages = math.ceil(len(images) / items_per_page)
    
    template = env.get_template('index.html')
    
    for page_num in range(1, total_pages + 1):
        start_idx = (page_num - 1) * items_per_page
        end_idx = start_idx + items_per_page
        page_images = images[start_idx:end_idx]
        
        html = template.render(
            images=page_images,
            total_images=len(images),
            current_page=page_num,
            total_pages=total_pages
        )
        
        # First page is index.html, others are page_2.html, page_3.html, etc.
        if page_num == 1:
            output_file = Path(CONFIG['output_dir']) / 'index.html'
        else:
            output_file = Path(CONFIG['output_dir']) / f'page_{page_num}.html'
        
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
    
    # Load tag categories and generate CSS
    tag_to_category, category_colors = load_tag_categories()
    generate_tag_css(category_colors)
    
    # Setup Jinja2
    env = Environment(loader=FileSystemLoader(CONFIG['template_dir']))
    
    # Register tag_to_slug as a Jinja2 filter
    env.filters['slugify'] = tag_to_slug
    
    # Generate paginated homepage
    print("\n📄 Generating homepage...")
    generate_homepage_pages(env, images)
    
    # Generate individual image pages
    print("📄 Generating image pages...")
    for image in images:
        generate_image_page(env, image, images, all_tags_dict, tag_to_category)
    
    # Generate paginated tag pages
    print("📄 Generating tag pages...")
    for tag, count in all_tags_list:
        tagged_images = [img for img in images if tag in img['tags']]
        generate_tag_pages(env, tag, tagged_images)
    
    # Cleanup orphaned files
    print("\n🧹 Cleaning up orphaned files...")
    cleanup_orphaned_files(images, all_tags_list)
    
    print(f"\n✅ Generated gallery!")
    print(f"   📸 {len(images)} image pages")
    print(f"   🏷️  {len(all_tags_list)} tag pages (paginated)")
    print(f"   📁 Thumbnails saved to {CONFIG['output_dir']}/{CONFIG['thumbnail_dir']}/")
    print(f"   📁 Output saved to {CONFIG['output_dir']}/")

if __name__ == '__main__':
    generate_site()