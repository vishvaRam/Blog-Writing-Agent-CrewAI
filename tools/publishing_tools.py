"""
Publishing Tools for CrewAI Blog Automation
Tools for publishing content to Medium and other platforms
"""

import os
import json
import requests
from typing import Dict, List, Any, Optional
from crewai.tools import BaseTool
import time
import re


class MediumPublisherTool(BaseTool):
    name: str = "Medium Content Publisher"
    description: str = "Publish formatted blog posts to Medium platform with proper metadata and formatting"
    
    def __init__(self):
        self.integration_token = os.getenv('MEDIUM_INTEGRATION_TOKEN')
        if not self.integration_token:
            raise ValueError("MEDIUM_INTEGRATION_TOKEN environment variable is required")
        self.base_url = "https://api.medium.com/v1"
        
    def _run(self, title: str, content: str, tags: str = "", publish_status: str = "draft") -> str:
        """
        Publish content to Medium
        
        Args:
            title: Blog post title
            content: Blog post content in Markdown format
            tags: Comma-separated tags (max 5)
            publish_status: 'public', 'draft', or 'unlisted'
        """
        try:
            # Get user information
            user_info = self._get_user_info()
            if 'error' in user_info:
                return json.dumps(user_info)
            
            user_id = user_info['id']
            
            # Process and format content for Medium
            formatted_content = self._format_content_for_medium(content)
            
            # Process tags
            tags_list = self._process_tags(tags)
            
            # Create the post
            post_data = {
                'title': title,
                'contentFormat': 'markdown',
                'content': formatted_content,
                'tags': tags_list,
                'publishStatus': publish_status.lower()
            }
            
            # Publish the post
            response = self._create_post(user_id, post_data)
            
            if 'error' in response:
                return json.dumps(response)
            
            # Get additional post information
            post_info = self._get_post_info(response)
            
            return json.dumps({
                'success': True,
                'post_id': response['id'],
                'title': title,
                'medium_url': response['url'],
                'publish_status': publish_status,
                'tags': tags_list,
                'publication_date': time.time(),
                'user_info': {
                    'username': user_info.get('username', ''),
                    'name': user_info.get('name', '')
                },
                'post_details': post_info,
                'content_stats': self._analyze_content_stats(formatted_content)
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                'error': f"Error publishing to Medium: {str(e)}",
                'title': title,
                'success': False
            })
    
    def _get_user_info(self) -> Dict[str, Any]:
        """Get authenticated user information"""
        try:
            headers = {
                'Authorization': f'Bearer {self.integration_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            response = requests.get(f'{self.base_url}/me', headers=headers, timeout=10)
            response.raise_for_status()
            
            return response.json()['data']
            
        except requests.RequestException as e:
            return {'error': f"Failed to get user info: {str(e)}"}
        except Exception as e:
            return {'error': f"Error getting user info: {str(e)}"}
    
    def _format_content_for_medium(self, content: str) -> str:
        """Format content for Medium's markdown requirements"""
        
        formatted_content = content
        
        # Ensure proper line breaks around headings
        formatted_content = re.sub(r'\n(#+\s)', r'\n\n\1', formatted_content)
        formatted_content = re.sub(r'(#+\s.+)\n([^\n])', r'\1\n\n\2', formatted_content)
        
        # Fix multiple consecutive newlines (Medium prefers double line breaks)
        formatted_content = re.sub(r'\n{3,}', '\n\n', formatted_content)
        
        # Ensure proper formatting for lists
        formatted_content = re.sub(r'\n(\*|\-|\d+\.)\s', r'\n\n\1 ', formatted_content)
        
        # Add proper spacing around code blocks
        formatted_content = re.sub(r'\n```', r'\n\n```', formatted_content)
        formatted_content = re.sub(r'```\n', r'```\n\n', formatted_content)
        
        # Ensure blockquotes have proper spacing
        formatted_content = re.sub(r'\n>', r'\n\n>', formatted_content)
        
        # Clean up any excessive whitespace
        formatted_content = re.sub(r'[ \t]+\n', '\n', formatted_content)
        
        return formatted_content.strip()
    
    def _process_tags(self, tags_string: str, max_tags: int = 5) -> List[str]:
        """Process and validate tags for Medium"""
        
        if not tags_string:
            return []
        
        # Split by comma and clean
        tags = [tag.strip() for tag in tags_string.split(',') if tag.strip()]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_tags = []
        for tag in tags:
            tag_lower = tag.lower()
            if tag_lower not in seen and len(tag) <= 25:  # Medium tag length limit
                seen.add(tag_lower)
                unique_tags.append(tag)
        
        # Limit to max_tags
        return unique_tags[:max_tags]
    
    def _create_post(self, user_id: str, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create post on Medium"""
        try:
            headers = {
                'Authorization': f'Bearer {self.integration_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            response = requests.post(
                f'{self.base_url}/users/{user_id}/posts',
                headers=headers,
                json=post_data,
                timeout=30
            )
            
            if response.status_code == 201:
                return response.json()['data']
            else:
                return {
                    'error': f"Failed to create post: {response.status_code} - {response.text}",
                    'status_code': response.status_code
                }
                
        except requests.RequestException as e:
            return {'error': f"Network error creating post: {str(e)}"}
        except Exception as e:
            return {'error': f"Error creating post: {str(e)}"}
    
    def _get_post_info(self, post_response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and format post information"""
        
        return {
            'id': post_response.get('id', ''),
            'title': post_response.get('title', ''),
            'author_id': post_response.get('authorId', ''),
            'url': post_response.get('url', ''),
            'canonical_url': post_response.get('canonicalUrl', ''),
            'publish_status': post_response.get('publishStatus', ''),
            'published_at': post_response.get('publishedAt', ''),
            'license': post_response.get('license', ''),
            'license_url': post_response.get('licenseUrl', '')
        }
    
    def _analyze_content_stats(self, content: str) -> Dict[str, Any]:
        """Analyze content statistics for reporting"""
        
        word_count = len(content.split())
        char_count = len(content)
        paragraph_count = len([p for p in content.split('\n\n') if p.strip()])
        
        # Count different elements
        heading_count = len(re.findall(r'^#+\s', content, re.MULTILINE))
        link_count = len(re.findall(r'\[([^\]]+)\]\([^)]+\)', content))
        image_count = content.count('![')
        code_block_count = content.count('```')
        
        # Estimate reading time (200 words per minute)
        estimated_read_time = max(1, round(word_count / 200))
        
        return {
            'word_count': word_count,
            'character_count': char_count,
            'paragraph_count': paragraph_count,
            'heading_count': heading_count,
            'link_count': link_count,
            'image_count': image_count,
            'code_block_count': code_block_count,
            'estimated_read_time_minutes': estimated_read_time
        }


class ContentFormatterTool(BaseTool):
    name: str = "Content Formatter"
    description: str = "Format content for different publishing platforms with platform-specific optimizations"
    
    def _run(self, content: str, platform: str = "medium", title: str = "", author: str = "") -> str:
        """
        Format content for specific platforms
        
        Args:
            content: Raw content to format
            platform: Target platform (medium, wordpress, ghost, etc.)
            title: Post title
            author: Author name
        """
        try:
            if platform.lower() == "medium":
                formatted_content = self._format_for_medium(content, title, author)
            elif platform.lower() == "wordpress":
                formatted_content = self._format_for_wordpress(content, title, author)
            else:
                formatted_content = self._format_generic(content, title, author)
            
            return json.dumps({
                'platform': platform,
                'title': title,
                'author': author,
                'original_content': content,
                'formatted_content': formatted_content,
                'formatting_applied': self._get_formatting_summary(content, formatted_content),
                'content_stats': self._get_content_stats(formatted_content)
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                'error': f"Error formatting content: {str(e)}",
                'platform': platform,
                'title': title
            })
    
    def _format_for_medium(self, content: str, title: str, author: str) -> str:
        """Format content specifically for Medium"""
        
        formatted = content
        
        # Add title if not present
        if title and not content.startswith('#'):
            formatted = f"# {title}\n\n{formatted}"
        
        # Ensure proper paragraph spacing (Medium prefers double line breaks)
        formatted = re.sub(r'\n{3,}', '\n\n', formatted)
        
        # Format emphasis properly
        formatted = re.sub(r'\*\*(.*?)\*\*', r'**\1**', formatted)  # Bold
        formatted = re.sub(r'\*(.*?)\*', r'*\1*', formatted)  # Italics
        
        # Format blockquotes with proper spacing
        formatted = re.sub(r'\n>', r'\n\n>', formatted)
        formatted = re.sub(r'>\s*\n([^>])', r'>\n\n\1', formatted)
        
        # Format code blocks
        formatted = re.sub(r'\n```', r'\n\n```', formatted)
        formatted = re.sub(r'```\n', r'```\n\n', formatted)
        
        # Format lists properly
        formatted = re.sub(r'\n(\*|\-|\d+\.)\s', r'\n\n\1 ', formatted)
        
        # Add author attribution if provided
        if author:
            formatted += f"\n\n---\n\n*Written by {author}*"
        
        return formatted.strip()
    
    def _format_for_wordpress(self, content: str, title: str, author: str) -> str:
        """Format content for WordPress"""
        
        formatted = content
        
        # WordPress can handle tighter spacing
        formatted = re.sub(r'\n{4,}', '\n\n\n', formatted)
        
        # Add WordPress-specific shortcodes if needed
        # (This would be expanded based on specific WordPress setup)
        
        # Format images with WordPress classes
        formatted = re.sub(r'!\[(.*?)\]\((.*?)\)', r'![\\1](\\2){.wp-image}', formatted)
        
        return formatted.strip()
    
    def _format_generic(self, content: str, title: str, author: str) -> str:
        """Generic formatting for other platforms"""
        
        formatted = content
        
        # Basic cleanup
        formatted = re.sub(r'\n{3,}', '\n\n', formatted)
        formatted = re.sub(r'[ \t]+\n', '\n', formatted)
        
        return formatted.strip()
    
    def _get_formatting_summary(self, original: str, formatted: str) -> Dict[str, Any]:
        """Summarize formatting changes applied"""
        
        original_lines = len(original.split('\n'))
        formatted_lines = len(formatted.split('\n'))
        
        return {
            'original_line_count': original_lines,
            'formatted_line_count': formatted_lines,
            'line_difference': formatted_lines - original_lines,
            'formatting_changes_applied': True
        }
    
    def _get_content_stats(self, content: str) -> Dict[str, Any]:
        """Get statistics about formatted content"""
        
        return {
            'word_count': len(content.split()),
            'character_count': len(content),
            'paragraph_count': len([p for p in content.split('\n\n') if p.strip()]),
            'heading_count': len(re.findall(r'^#+\s', content, re.MULTILINE)),
            'link_count': len(re.findall(r'\[([^\]]+)\]\([^)]+\)', content)),
            'image_count': content.count('!['),
            'emphasis_count': content.count('**') + content.count('*')
        }


class PublicationTrackerTool(BaseTool):
    name: str = "Publication Tracker"
    description: str = "Track publication success and performance metrics across platforms"
    
    def _run(self, publication_data: str, platform: str = "medium") -> str:
        """
        Track and analyze publication data
        
        Args:
            publication_data: JSON string with publication information
            platform: Publishing platform
        """
        try:
            data = json.loads(publication_data)
            
            tracking_report = {
                'platform': platform,
                'publication_timestamp': time.time(),
                'success': data.get('success', False),
                'post_url': data.get('medium_url', data.get('url', '')),
                'post_id': data.get('post_id', data.get('id', '')),
                'title': data.get('title', ''),
                'publish_status': data.get('publish_status', 'unknown'),
                'content_metrics': data.get('content_stats', {}),
                'engagement_setup': self._setup_engagement_tracking(data),
                'seo_checklist': self._create_seo_checklist(data),
                'follow_up_actions': self._generate_follow_up_actions(data)
            }
            
            return json.dumps(tracking_report, indent=2)
            
        except json.JSONDecodeError:
            return json.dumps({
                'error': 'Invalid JSON format in publication data',
                'platform': platform
            })
        except Exception as e:
            return json.dumps({
                'error': f"Error tracking publication: {str(e)}",
                'platform': platform
            })
    
    def _setup_engagement_tracking(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Set up engagement tracking configuration"""
        
        return {
            'post_url': data.get('medium_url', ''),
            'tracking_enabled': True,
            'metrics_to_track': [
                'views',
                'reads',
                'claps',
                'responses',
                'fans'
            ],
            'tracking_frequency': 'daily',
            'first_check_scheduled': time.time() + 86400  # 24 hours later
        }
    
    def _create_seo_checklist(self, data: Dict[str, Any]) -> Dict[str, bool]:
        """Create SEO checklist based on publication data"""
        
        content_stats = data.get('content_stats', {})
        
        checklist = {
            'title_optimized': len(data.get('title', '')) <= 60,
            'adequate_word_count': content_stats.get('word_count', 0) >= 1000,
            'has_headings': content_stats.get('heading_count', 0) >= 3,
            'has_links': content_stats.get('link_count', 0) > 0,
            'has_images': content_stats.get('image_count', 0) > 0,
            'proper_tags': len(data.get('tags', [])) >= 3,
            'published_successfully': data.get('success', False)
        }
        
        return checklist
    
    def _generate_follow_up_actions(self, data: Dict[str, Any]) -> List[str]:
        """Generate recommended follow-up actions"""
        
        actions = []
        
        if data.get('success', False):
            actions.extend([
                "Monitor post performance in first 24 hours",
                "Share on relevant social media platforms",
                "Engage with early commenters and claps",
                "Consider cross-posting to other platforms"
            ])
            
            # Platform-specific actions
            if 'medium_url' in data:
                actions.extend([
                    "Submit to relevant Medium publications",
                    "Add to your Medium highlights if it performs well",
                    "Consider writing a follow-up post on related topics"
                ])
        else:
            actions.extend([
                "Review error logs and fix issues",
                "Check API credentials and permissions",
                "Retry publication after fixing issues"
            ])
        
        return actions