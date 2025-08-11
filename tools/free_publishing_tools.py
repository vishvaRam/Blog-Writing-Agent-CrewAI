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
    description: str = "Publish blog posts to Dev.to platform (FREE)"
    api_key: Optional[str] = Field(default=None, exclude=True)
    base_url: str = "https://dev.to/api"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_key = os.getenv('DEVTO_API_KEY')
        if not self.api_key:
            print("⚠️ Warning: DEVTO_API_KEY not found in environment variables")
        
    def _run(self, title: str, content: str, tags: str = "", published: bool = False) -> str:
        """
        Publish content to Dev.to
        
        Args:
            title: Blog post title
            content: Blog post content in Markdown
            tags: Comma-separated tags (max 4)
            published: True to publish immediately, False for draft
        """
        if not self.api_key:
            return json.dumps({
                'success': False,
                'error': 'DEVTO_API_KEY environment variable not set',
                'setup_instructions': [
                    '1. Visit https://dev.to/settings/extensions',
                    '2. Scroll to "DEV Community API Keys"',
                    '3. Generate new API key',
                    '4. Set DEVTO_API_KEY environment variable',
                    '5. Example: export DEVTO_API_KEY="your_api_key_here"'
                ]
            })
        
        try:
            # Process tags (Dev.to allows max 4 tags)
            tags_list = []
            if tags:
                tags_list = [tag.strip().lower() for tag in tags.split(',') if tag.strip()][:4]
            
            # Clean content - ensure proper markdown format
            cleaned_content = content.strip()
            
            # Create article data with correct Dev.to API format
            article_data = {
                "article": {
                    "title": title.strip(),
                    "body_markdown": cleaned_content,
                    "published": published,
                    "tags": tags_list,
                    "series": None,  # Optional: can be used for series
                    "main_image": None,  # Optional: main image URL
                    "canonical_url": None,  # Optional: if republishing
                    "description": ""  # Optional: meta description
                }
            }
            
            # Set correct headers
            headers = {
                "api-key": self.api_key,
                "Content-Type": "application/json",
                "Accept": "application/vnd.forem.api-v1+json"
            }
            
            print(f"📤 Publishing '{title}' to Dev.to...")
            print(f"🏷️ Tags: {tags_list}")
            print(f"📊 Status: {'Published' if published else 'Draft'}")
            
            # Make API request to correct endpoint
            response = requests.post(
                f"{self.base_url}/articles",
                headers=headers,
                json=article_data,
                timeout=30
            )
            
            print(f"📡 API Response Status: {response.status_code}")
            
            if response.status_code == 201:
                article = response.json()
                status = "published" if published else "draft"
                
                result = {
                    'success': True,
                    'platform': 'dev.to',
                    'article_id': article.get('id'),
                    'url': article.get('url', ''),
                    'slug': article.get('slug', ''),
                    'status': status,
                    'title': title,
                    'tags': tags_list,
                    'published_at': article.get('published_at'),
                    'created_at': article.get('created_at'),
                    'reading_time_minutes': article.get('reading_time_minutes'),
                    'public_reactions_count': article.get('public_reactions_count', 0),
                    'page_views_count': article.get('page_views_count', 0),
                    'user': article.get('user', {})
                }
                
                print(f"✅ Successfully published to Dev.to!")
                print(f"🔗 URL: {result['url']}")
                
                return json.dumps(result, indent=2)
                
            elif response.status_code == 401:
                return json.dumps({
                    'success': False,
                    'error': 'Authentication failed - check your Dev.to API key',
                    'status_code': response.status_code,
                    'title': title,
                    'troubleshooting': [
                        'Verify your API key is correct',
                        'Check if API key has expired',
                        'Ensure you have write permissions',
                        'Try generating a new API key'
                    ]
                })
                
            elif response.status_code == 422:
                error_data = response.json() if response.content else {}
                return json.dumps({
                    'success': False,
                    'error': 'Validation error - check your content format',
                    'status_code': response.status_code,
                    'validation_errors': error_data,
                    'title': title,
                    'troubleshooting': [
                        'Check if title is too long (max 128 characters)',
                        'Verify tags are valid (no special characters)',
                        'Ensure content is valid markdown',
                        'Check for duplicate titles'
                    ]
                })
                
            else:
                error_text = response.text[:500] if response.content else "No response body"
                return json.dumps({
                    'success': False,
                    'error': f"Failed to publish to Dev.to: HTTP {response.status_code}",
                    'status_code': response.status_code,
                    'response_preview': error_text,
                    'title': title
                })
                
        except requests.exceptions.Timeout:
            return json.dumps({
                'success': False,
                'error': 'Request timeout - Dev.to API took too long to respond',
                'title': title
            })
            
        except requests.exceptions.ConnectionError:
            return json.dumps({
                'success': False,
                'error': 'Connection error - check your internet connection',
                'title': title
            })
            
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': f"Unexpected error publishing to Dev.to: {str(e)}",
                'title': title,
                'error_type': type(e).__name__
            })


class HashnodePublisherTool(BaseTool):
    name: str = "Hashnode Publisher"
    description: str = "Publish blog posts to Hashnode platform (FREE)"
    api_token: Optional[str] = Field(default=None, exclude=True)
    api_url: str = "https://api.hashnode.com/v1"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_token = os.getenv('HASHNODE_TOKEN')
        self.api_url = "https://gql.hashnode.com"
        
    def _run(self, title: str, content: str, tags: str = "", published: bool = False) -> str:
        """
        Publish content to Hashnode
        
        Args:
            title: Blog post title
            content: Blog post content in Markdown
            tags: Comma-separated tags
            published: True to publish immediately, False for draft
        """
        if not self.api_token:
            return json.dumps({
                'error': 'HASHNODE_TOKEN environment variable not set',
                'setup_instructions': [
                    '1. Visit https://hashnode.com/settings/developer',
                    '2. Generate Personal Access Token',
                    '3. Set HASHNODE_TOKEN environment variable'
                ]
            })
        
        try:
            # Process tags for Hashnode
            tags_list = [{"name": tag.strip()} for tag in tags.split(',') if tag.strip()][:5]
            
            # GraphQL mutation for publishing
            mutation = """
            mutation PublishPost($input: PublishPostInput!) {
                publishPost(input: $input) {
                    post {
                        id
                        title
                        url
                        publishedAt
                        slug
                    }
                }
            }
            """
            
            # Prepare variables
            variables = {
                "input": {
                    "title": title,
                    "contentMarkdown": content,
                    "tags": tags_list,
                    "publishedAt": datetime.now().isoformat() if published else None
                }
            }
            
            # Make GraphQL request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_token}"
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json={
                    "query": mutation,
                    "variables": variables
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'errors' in data:
                    return json.dumps({
                        'error': 'GraphQL errors in Hashnode API',
                        'errors': data['errors'],
                        'title': title
                    })
                
                post = data['data']['publishPost']['post']
                
                return json.dumps({
                    'success': True,
                    'platform': 'hashnode',
                    'post_id': post['id'],
                    'url': post['url'],
                    'slug': post['slug'],
                    'title': post['title'],
                    'status': 'published' if published else 'draft',
                    'published_at': post.get('publishedAt'),
                    'tags': [tag['name'] for tag in tags_list]
                }, indent=2)
            else:
                return json.dumps({
                    'error': f"Failed to publish to Hashnode: {response.status_code}",
                    'response': response.text[:500],
                    'title': title
                })
                
        except Exception as e:
            return json.dumps({
                'error': f"Error publishing to Hashnode: {str(e)}",
                'title': title
            })


class PublishingOrchestratorTool(BaseTool):
    name: str = "Publishing Orchestrator"
    description: str = "Orchestrate the complete publishing workflow: save locally, then publish to selected free platforms"
    
    def _run(self, blog_data: str, images_data: str = "", platforms: str = "devto", published: bool = False) -> str:
        """Complete publishing workflow with better error handling"""
        try:
            # Parse blog data
            blog_info = json.loads(blog_data)
            title = blog_info.get('title', '')
            content = blog_info.get('content', '')
            topic = blog_info.get('topic', '')
            tags = blog_info.get('tags', '')
            
            print(f"🚀 Starting publishing workflow for: '{title}'")
            
            results = {
                'workflow_started': datetime.now().isoformat(),
                'title': title,
                'topic': topic,
                'platforms_requested': platforms.split(','),
                'results': {},
                'environment_check': self._check_environment()
            }
            
            # Step 1: Always save locally first
            print("📁 Saving blog post locally...")
            local_saver = LocalBlogSaverTool()
            local_result = local_saver._run(title, content, images_data, topic)
            local_data = json.loads(local_result)
            results['results']['local'] = local_data
            
            if not local_data.get('success'):
                return json.dumps({
                    'error': 'Failed to save locally - aborting workflow',
                    'details': local_data
                })
            
            print(f"✅ Blog saved locally at: {local_data['blog_directory']}")
            
            # Step 2: Publish to requested platforms
            requested_platforms = [p.strip().lower() for p in platforms.split(',')]
            
            if 'devto' in requested_platforms:
                print("🚀 Publishing to Dev.to...")
                devto_publisher = DevToPublisherTool()
                devto_result = devto_publisher._run(title, content, tags, published)
                devto_data = json.loads(devto_result)
                results['results']['devto'] = devto_data
                
                if devto_data.get('success'):
                    print(f"✅ Dev.to: {devto_data.get('url', 'Published successfully')}")
                else:
                    print(f"❌ Dev.to failed: {devto_data.get('error', 'Unknown error')}")
            
            if 'hashnode' in requested_platforms:
                print("🚀 Publishing to Hashnode...")
                hashnode_publisher = HashnodePublisherTool()
                hashnode_result = hashnode_publisher._run(title, content, tags, published)
                hashnode_data = json.loads(hashnode_result)
                results['results']['hashnode'] = hashnode_data
                
                if hashnode_data.get('success'):
                    print(f"✅ Hashnode: {hashnode_data.get('url', 'Published successfully')}")
                else:
                    print(f"❌ Hashnode failed: {hashnode_data.get('error', 'Unknown error')}")
            
            # Generate summary
            successful_platforms = []
            failed_platforms = []
            
            for platform, result in results['results'].items():
                if result.get('success'):
                    successful_platforms.append(platform)
                else:
                    failed_platforms.append(platform)
            
            results['summary'] = {
                'total_platforms': len(results['results']),
                'successful_platforms': successful_platforms,
                'failed_platforms': failed_platforms,
                'success_rate': len(successful_platforms) / len(results['results']) * 100,
                'local_directory': local_data.get('blog_directory'),
                'next_steps': self._generate_next_steps(results['results'])
            }
            
            print(f"📊 Summary: {len(successful_platforms)}/{len(results['results'])} platforms successful")
            
            return json.dumps(results, indent=2)
            
        except json.JSONDecodeError:
            return json.dumps({
                'error': 'Invalid JSON format in blog_data or images_data'
            })
        except Exception as e:
            return json.dumps({
                'error': f"Error in publishing orchestrator: {str(e)}",
                'error_type': type(e).__name__
            })
    
    def _check_environment(self) -> Dict[str, Any]:
        """Check if required environment variables are set"""
        
        env_check = {
            'devto_api_key_set': bool(os.getenv('DEVTO_API_KEY')),
            'hashnode_token_set': bool(os.getenv('HASHNODE_TOKEN')),
            'recommendations': []
        }
        
        if not env_check['devto_api_key_set']:
            env_check['recommendations'].append('Set DEVTO_API_KEY for Dev.to publishing')
            
        if not env_check['hashnode_token_set']:
            env_check['recommendations'].append('Set HASHNODE_TOKEN for Hashnode publishing')
        
        return env_check
    
    def _generate_next_steps(self, results: Dict[str, Any]) -> List[str]:
        """Generate next steps based on results"""
        
        next_steps = []
        
        # Always include local review step
        if results.get('local', {}).get('success'):
            local_dir = results['local']['blog_directory']
            next_steps.append(f"📝 Review your blog post at: {local_dir}")
            next_steps.append(f"📋 Check publication instructions: {local_dir}/publication_instructions.md")
        
        # Add platform-specific steps
        for platform, result in results.items():
            if platform == 'local':
                continue
                
            if result.get('success'):
                url = result.get('url', '')
                if url:
                    next_steps.append(f"✅ {platform.title()} published: {url}")
                else:
                    next_steps.append(f"✅ {platform.title()} published successfully")
            else:
                error = result.get('error', 'Unknown error')
                next_steps.append(f"❌ {platform.title()} failed: {error}")
        
        # Add general recommendations
        next_steps.extend([
            "🖼️ Download images using the provided script",
            "📊 Monitor post performance after 24 hours", 
            "🔗 Share on social media for maximum reach"
        ])
        
        return next_steps
