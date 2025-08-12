"""
Free Publishing Tools for CrewAI Blog Automation
Modified to save locally first and publish to free platforms like Dev.to
"""

import os
import json
import requests
from typing import Dict, List, Any, Optional
from crewai.tools import BaseTool
from pydantic import Field
import time
import re
from pathlib import Path
from datetime import datetime
from pydantic import Field



class LocalBlogSaverTool(BaseTool):
    name: str = "Local Blog Saver"
    description: str = "Save generated blog posts locally with images and metadata"
    
    def _run(self, title: str, content: str, images_data: str = "", topic: str = "") -> str:
        """
        Save blog post locally in organized structure
        
        Args:
            title: Blog post title
            content: Blog post content in Markdown
            images_data: JSON string with image information
            topic: Original topic for organization
        """
        try:
            # Create organized directory structure
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_topic = safe_topic.replace(' ', '-').lower()
            
            # Create directories
            base_dir = Path('local_blogs')
            blog_dir = base_dir / f"{timestamp}_{safe_topic}"
            blog_dir.mkdir(parents=True, exist_ok=True)
            
            # Save main blog post
            blog_file = blog_dir / 'blog_post.md'
            with open(blog_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Save metadata
            metadata = {
                'title': title,
                'topic': topic,
                'created_at': timestamp,
                'word_count': len(content.split()),
                'char_count': len(content),
                'estimated_read_time': max(1, len(content.split()) // 200),
                'status': 'draft',
                'platforms': {
                    'devto': {'published': False, 'url': ''},
                    'hashnode': {'published': False, 'url': ''},
                    'local_saved': True
                }
            }
            
            metadata_file = blog_dir / 'metadata.json'
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            # Process and save images
            if images_data:
                try:
                    images = json.loads(images_data)
                    images_dir = blog_dir / 'images'
                    images_dir.mkdir(exist_ok=True)
                    
                    # Save image metadata
                    image_metadata_file = images_dir / 'images_metadata.json'
                    with open(image_metadata_file, 'w', encoding='utf-8') as f:
                        json.dump(images, f, indent=2)
                    
                    # Create image download instructions
                    download_script = self._create_image_download_script(images, images_dir)
                    download_script_file = images_dir / 'download_images.py'
                    with open(download_script_file, 'w', encoding='utf-8') as f:
                        f.write(download_script)
                    
                except json.JSONDecodeError:
                    pass  # Skip images if invalid JSON
            
            # Create publication instructions
            pub_instructions = self._create_publication_instructions(title, blog_file, metadata)
            instructions_file = blog_dir / 'publication_instructions.md'
            with open(instructions_file, 'w', encoding='utf-8') as f:
                f.write(pub_instructions)
            
            return json.dumps({
                'success': True,
                'blog_directory': str(blog_dir),
                'files_created': {
                    'blog_post': str(blog_file),
                    'metadata': str(metadata_file),
                    'instructions': str(instructions_file),
                    'images_dir': str(blog_dir / 'images') if images_data else None
                },
                'metadata': metadata,
                'next_steps': [
                    f"Review the blog post at: {blog_file}",
                    f"Check publication instructions: {instructions_file}",
                    "Edit content if needed before publishing",
                    "Run the publishing script when ready"
                ]
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                'error': f"Error saving blog locally: {str(e)}",
                'title': title
            })
    
    def _create_image_download_script(self, images_data: Dict, images_dir: Path) -> str:
        """Create Python script to download images"""
        
        script = '''#!/usr/bin/env python3
"""
Script to download images for the blog post
Run this script to download all images locally
"""

import requests
import os
from pathlib import Path

def download_image(url, filename):
    """Download image from URL"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Downloaded: {filename}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to download {url}: {str(e)}")
        return False

def main():
    """Download all images"""
    images_to_download = [
'''
        
        # Add image download data
        if 'optimized_images' in images_data:
            for img in images_data['optimized_images']:
                script += f'        {{\n'
                script += f'            "url": "{img.get("download_url", "")}",\n'
                script += f'            "filename": "{img.get("file_name", "image.jpg")}",\n'
                script += f'            "alt_text": "{img.get("alt_text", "")}"\n'
                script += f'        }},\n'
        
        script += '''    ]
    
    print(f"📥 Downloading {len(images_to_download)} images...")
    
    success_count = 0
    for img in images_to_download:
        if download_image(img["url"], img["filename"]):
            success_count += 1
    
    print(f"\\n✅ Downloaded {success_count}/{len(images_to_download)} images successfully")

if __name__ == "__main__":
    main()
'''
        
        return script
    
    def _create_publication_instructions(self, title: str, blog_file: Path, metadata: Dict) -> str:
        """Create instructions for publishing to various platforms"""
        
        instructions = f'''# Publication Instructions for: {title}

## 📁 Files Overview
- **Blog Post**: `{blog_file.name}`
- **Metadata**: `metadata.json`
- **Images**: `images/` directory (run `python images/download_images.py` first)

## 🚀 Publishing Options

### Option 1: Dev.to (Recommended - FREE)

1. **Get API Key**:
   - Visit: https://dev.to/settings/account
   - Scroll to "DEV Community API Keys"
   - Generate new API key

2. **Publish via API**:
   ```bash
   # Set your API key
   export DEVTO_API_KEY="your_api_key_here"
   
   # Run the Dev.to publishing script
   python ../publish_to_devto.py
   ```

3. **Manual Publishing**:
   - Copy content from `{blog_file.name}`
   - Go to https://dev.to/new
   - Paste content and publish

### Option 2: Hashnode (FREE)

1. **Get API Token**:
   - Visit: https://hashnode.com/settings/developer
   - Generate Personal Access Token

2. **Publish via GraphQL API**:
   ```bash
   export HASHNODE_TOKEN="your_token_here"
   python ../publish_to_hashnode.py
   ```

### Option 3: GitHub Pages (FREE)

1. **Setup Repository**:
   - Create GitHub repository: `username.github.io`
   - Enable GitHub Pages in settings

2. **Add Blog Post**:
   ```bash
   # Copy to Jekyll _posts directory
   cp {blog_file.name} ../_posts/{datetime.now().strftime("%Y-%m-%d")}-{title.lower().replace(" ", "-")}.md
   ```

### Option 4: Manual Publishing

Copy the content and publish manually to any platform:
- **Medium**: https://medium.com/new-story
- **LinkedIn Articles**: https://www.linkedin.com/pulse/new/
- **Personal Website**: Copy to your blog directory

## ✅ Pre-Publication Checklist

- [ ] Review content for accuracy and readability
- [ ] Download images using `python images/download_images.py`
- [ ] Check image attributions are included
- [ ] Verify all links work correctly
- [ ] Add relevant tags for the platform
- [ ] Set appropriate publication status (draft/published)

## 📊 Blog Statistics

- **Word Count**: {metadata.get("word_count", "N/A")}
- **Estimated Read Time**: {metadata.get("estimated_read_time", "N/A")} minutes
- **Created**: {metadata.get("created_at", "N/A")}

## 🏷️ Suggested Tags

Based on your topic "{metadata.get("topic", "")}", consider these tags:
- {metadata.get("topic", "").lower().replace(" ", "")}
- programming
- technology
- ai
- tutorial

Happy publishing! 🎉
'''
        
        return instructions


class DevToPublisherTool(BaseTool):
    name: str = "Dev.to Publisher"
    description: str = "Publish blog posts to Dev.to platform"
    api_key: str = os.getenv('DEVTO_API_KEY')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_key = os.getenv('DEVTO_API_KEY')
        
    def _run(self, blog_data: str) -> str:
        """
        Publish content to Dev.to - Fixed input handling
        
        Args:
            blog_data: JSON string containing title, content, tags, and published status
        """
        if not self.api_key:
            return json.dumps({
                'success': False,
                'error': 'DEVTO_API_KEY not found'
            })
        
        try:
            # Parse the input data
            if isinstance(blog_data, str):
                data = json.loads(blog_data)
            else:
                data = blog_data
                
            title = data.get('title', '')
            content = data.get('content', '')
            tags = data.get('tags', '')
            published = data.get('published', True)  # Default to True for direct publishing
            
            # Process tags
            tags_list = [tag.strip().lower() for tag in tags.split(',')][:4] if tags else []
            
            # API payload
            article_data = {
                "article": {
                    "title": title[:128],
                    "body_markdown": content,
                    "published": published,
                    "tags": tags_list
                }
            }
            
            # Headers
            headers = {
                "api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            # Make API call
            response = requests.post(
                "https://dev.to/api/articles",
                headers=headers,
                json=article_data,
                timeout=15
            )
            
            if response.status_code == 201:
                article = response.json()
                return json.dumps({
                    'success': True,
                    'url': article.get('url', ''),
                    'id': article.get('id'),
                    'status': 'published' if published else 'draft'
                })
            else:
                return json.dumps({
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'details': response.text[:200]
                })
                
        except json.JSONDecodeError:
            return json.dumps({
                'success': False,
                'error': 'Invalid JSON input format'
            })
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': str(e)
            })


