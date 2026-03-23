#!/usr/bin/env python3
"""
Build script to generate static HTML gallery from metadata.json
"""

import json
import os
from pathlib import Path
from jinja2 import Template

# Configuration
IMAGES_DIR = Path("images")
METADATA_FILE = Path("metadata.json")
DOCS_DIR = Path("docs")

def load_metadata():
    """Load metadata from JSON file"""
    with open(METADATA_FILE, 'r') as f:
        return json.load(f)

def get_all_tags(images):
    """Extract all unique tags from images"""
    tags = set()
    for image in images:
        tags.update(image.get('tags', []))
    return sorted(list(tags))

def generate_index(data):
    """Generate main index.html"""
    images = data['images']
    tags = get_all_tags(images)
    
    html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ site_title }}</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>{{ site_title }}</h1>
            <p>{{ site_description }}</p>
        </header>

        <div class="controls">
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="Search images...">
            </div>
            
            <div class="tag-filter">
                <h3>Tags</h3>
                <div class="tag-list">
                    {% for tag in tags %}
                    <button class="tag-btn" data-tag="{{ tag }}">{{ tag }}</button>
                    {% endfor %}
                </div>
                <button id="clearFilter" class="clear-btn">Clear All</button>
            </div>
        </div>

        <main class="gallery">
            {% for image in images %}
            <div class="image-card" data-tags="{{ image.tags|join(',') }}" data-title="{{ image.title|lower }}" data-description="{{ image.description|lower }}">
                <div class="image-container">
                    <img src="../images/{{ image.filename }}" alt="{{ image.title }}">
                </div>
                <div class="image-info">
                    <h3>{{ image.title }}</h3>
                    <p>{{ image.description }}</p>
                    <div class="tags">
                        {% for tag in image.tags %}
                        <span class="tag">{{ tag }}</span>
                        {% endfor %}
                    </div>
                </div>
            </div>
            {% endfor %}
        </main>
    </div>

    <script src="gallery.js"></script>
</body>
</html>'''
    
    template = Template(html_template)
    html_content = template.render(
        site_title=data.get('site_title', 'Image Gallery'),
        site_description=data.get('site_description', 'A tagged image gallery'),
        images=images,
        tags=tags
    )
    
    output_file = DOCS_DIR / "index.html"
    output_file.write_text(html_content)
    print(f"✓ Generated {output_file}")

def main():
    """Main build function"""
    print("Building gallery...")
    
    # Create docs directory if it doesn't exist
    DOCS_DIR.mkdir(exist_ok=True)
    
    # Load metadata
    data = load_metadata()
    
    # Generate HTML
    generate_index(data)
    
    print("✓ Gallery built successfully!")
    print(f"  Output: {DOCS_DIR}/")

if __name__ == "__main__":
    main()