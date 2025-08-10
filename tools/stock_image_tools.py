"""
Stock Image Tools for CrewAI Blog Automation
Replaces AI image generation with curated stock images from Unsplash and Pexels
"""

import os
import json
import requests
from typing import List, Dict, Any, Optional
from crewai.tools import BaseTool
from urllib.parse import quote
import time
from pydantic import Field


# class UnsplashSearchTool(BaseTool):
#     name: str = "Unsplash Stock Image Search"
#     description: str = "Search for high-quality stock images from Unsplash based on topic keywords"
    
#     def __init__(self):
#         self.access_key = os.getenv('UNSPLASH_ACCESS_KEY')
#         if not self.access_key:
#             raise ValueError("UNSPLASH_ACCESS_KEY environment variable is required")
#         self.base_url = "https://api.unsplash.com"
        
#     def _run(self, query: str, count: int = 4, orientation: str = "landscape") -> str:
#         """
#         Search for stock images on Unsplash
        
#         Args:
#             query: Search terms for images
#             count: Number of images to return (max 30)
#             orientation: Image orientation (landscape, portrait, squarish)
#         """
#         try:
#             url = f"{self.base_url}/search/photos"
#             headers = {
#                 "Authorization": f"Client-ID {self.access_key}",
#                 "Accept-Version": "v1"
#             }
            
#             params = {
#                 "query": query,
#                 "per_page": min(count, 30),
#                 "orientation": orientation,
#                 "content_filter": "high",  # Filter for high quality images
#                 "order_by": "relevant"
#             }
            
#             response = requests.get(url, headers=headers, params=params, timeout=10)
#             response.raise_for_status()
            
#             data = response.json()
            
#             images = []
#             for photo in data.get('results', []):
#                 # Trigger download tracking (required by Unsplash API)
#                 self._trigger_download_tracking(photo['links']['download_location'])
                
#                 image_info = {
#                     'id': photo['id'],
#                     'description': photo.get('description', photo.get('alt_description', f"Stock photo related to {query}")),
#                     'urls': {
#                         'raw': photo['urls']['raw'],
#                         'full': photo['urls']['full'],
#                         'regular': photo['urls']['regular'],
#                         'small': photo['urls']['small'],
#                         'thumb': photo['urls']['thumb']
#                     },
#                     'photographer': {
#                         'name': photo['user']['name'],
#                         'username': photo['user']['username'],
#                         'profile': f"https://unsplash.com/@{photo['user']['username']}",
#                         'portfolio_url': photo['user'].get('portfolio_url', '')
#                     },
#                     'dimensions': {
#                         'width': photo['width'],
#                         'height': photo['height']
#                     },
#                     'color': photo.get('color', '#ffffff'),
#                     'downloads': photo.get('downloads', 0),
#                     'likes': photo.get('likes', 0),
#                     'unsplash_url': photo['links']['html'],
#                     'download_location': photo['links']['download_location'],
#                     'attribution': f"Photo by {photo['user']['name']} on Unsplash",
#                     'attribution_url': photo['links']['html'],
#                     'license': "Unsplash License (https://unsplash.com/license)",
#                     'source': 'unsplash'
#                 }
#                 images.append(image_info)
            
#             return json.dumps({
#                 "source": "unsplash",
#                 "total_results": data.get('total', 0),
#                 "images_returned": len(images),
#                 "images": images,
#                 "search_query": query,
#                 "search_timestamp": time.time()
#             }, indent=2)
            
#         except requests.RequestException as e:
#             return json.dumps({
#                 "error": f"Network error searching Unsplash: {str(e)}",
#                 "search_query": query,
#                 "source": "unsplash"
#             })
#         except Exception as e:
#             return json.dumps({
#                 "error": f"Error searching Unsplash: {str(e)}",
#                 "search_query": query,
#                 "source": "unsplash"
#             })
    
#     def _trigger_download_tracking(self, download_url: str):
#         """Trigger download tracking as required by Unsplash API"""
#         try:
#             headers = {"Authorization": f"Client-ID {self.access_key}"}
#             requests.get(download_url, headers=headers, timeout=5)
#         except:
#             pass  # Download tracking is best-effort


class PexelsSearchTool(BaseTool):
    name: str = "Pexels Stock Image Search"
    description: str = "Search for high-quality stock images from Pexels based on topic keywords"
    api_key: Optional[str] = Field(default=None, exclude=True)
    base_url: str = "https://api.pexels.com/v1"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_key = os.getenv('PEXELS_API_KEY')
        if not self.api_key:
            raise ValueError("PEXELS_API_KEY environment variable is required")
        self.base_url = "https://api.pexels.com/v1"
        
    def _run(self, query: str, count: int = 4, orientation: str = "landscape") -> str:
        """
        Search for stock images on Pexels
        
        Args:
            query: Search terms for images
            count: Number of images to return (max 80)
            orientation: Image orientation (landscape, portrait, square)
        """
        try:
            url = f"{self.base_url}/search"
            headers = {
                "Authorization": self.api_key
            }
            
            params = {
                "query": query,
                "per_page": min(count, 80),
                "orientation": orientation
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            images = []
            for photo in data.get('photos', []):
                image_info = {
                    'id': photo['id'],
                    'description': photo.get('alt', f"Professional stock photo related to {query}"),
                    'urls': {
                        'original': photo['src']['original'],
                        'large2x': photo['src']['large2x'],
                        'large': photo['src']['large'],
                        'medium': photo['src']['medium'],
                        'small': photo['src']['small'],
                        'portrait': photo['src']['portrait'],
                        'landscape': photo['src']['landscape'],
                        'tiny': photo['src']['tiny']
                    },
                    'photographer': {
                        'name': photo['photographer'],
                        'profile': photo['photographer_url']
                    },
                    'dimensions': {
                        'width': photo['width'],
                        'height': photo['height']
                    },
                    'average_color': photo.get('avg_color', '#ffffff'),
                    'pexels_url': photo['url'],
                    'attribution': f"Photo by {photo['photographer']} from Pexels",
                    'attribution_url': photo['url'],
                    'license': "Pexels License (https://www.pexels.com/license/)",
                    'source': 'pexels'
                }
                images.append(image_info)
            
            return json.dumps({
                "source": "pexels",
                "total_results": data.get('total_results', 0),
                "images_returned": len(images),
                "images": images,
                "search_query": query,
                "search_timestamp": time.time()
            }, indent=2)
            
        except requests.RequestException as e:
            return json.dumps({
                "error": f"Network error searching Pexels: {str(e)}",
                "search_query": query,
                "source": "pexels"
            })
        except Exception as e:
            return json.dumps({
                "error": f"Error searching Pexels: {str(e)}",
                "search_query": query,
                "source": "pexels"
            })


class ImageOptimizerTool(BaseTool):
    name: str = "Stock Image Optimizer and Curator"
    description: str = "Optimize and curate stock images for blog publication with SEO and attribution"
    
    def _run(self, image_data: str, blog_topic: str, blog_content: str = "") -> str:
        """
        Process and optimize stock images for blog use
        
        Args:
            image_data: JSON string containing image information from search tools
            blog_topic: The blog post topic for context
            blog_content: Optional blog content for better image selection
        """
        try:
            data = json.loads(image_data)
            
            if 'error' in data:
                return json.dumps({
                    'error': 'Cannot optimize images due to search error',
                    'original_error': data['error']
                })
            
            optimized_images = []
            images = data.get('images', [])
            
            if not images:
                return json.dumps({
                    'error': 'No images found to optimize',
                    'blog_topic': blog_topic
                })
            
            # Prioritize images for different uses
            for i, image in enumerate(images):
                usage_type = self._determine_image_usage(i, len(images))
                
                optimized = {
                    'id': image['id'],
                    'source': image.get('source', 'unknown'),
                    'usage_type': usage_type,
                    'recommended_size': self._get_recommended_size(usage_type),
                    'alt_text': self._generate_alt_text(image.get('description', ''), blog_topic, usage_type),
                    'file_name': self._generate_filename(blog_topic, image['id'], usage_type),
                    'download_url': self._select_optimal_url(image['urls'], usage_type),
                    'attribution': image.get('attribution', ''),
                    'attribution_url': image.get('attribution_url', ''),
                    'photographer': image.get('photographer', {}),
                    'license': image.get('license', ''),
                    'dimensions': image.get('dimensions', {}),
                    'placement_suggestion': self._suggest_placement(usage_type, i),
                    'seo_keywords': self._extract_seo_keywords(blog_topic, image.get('description', '')),
                    'caption_suggestion': self._generate_caption(image.get('description', ''), blog_topic)
                }
                optimized_images.append(optimized)
            
            return json.dumps({
                'blog_topic': blog_topic,
                'total_images': len(optimized_images),
                'featured_image': optimized_images[0] if optimized_images else None,
                'supporting_images': optimized_images[1:] if len(optimized_images) > 1 else [],
                'optimized_images': optimized_images,
                'attribution_block': self._generate_attribution_block(optimized_images),
                'seo_summary': self._generate_seo_summary(optimized_images),
                'optimization_timestamp': time.time()
            }, indent=2)
            
        except json.JSONDecodeError:
            return json.dumps({
                'error': 'Invalid JSON format in image data',
                'blog_topic': blog_topic
            })
        except Exception as e:
            return json.dumps({
                'error': f"Error optimizing images: {str(e)}",
                'blog_topic': blog_topic
            })
    
    def _determine_image_usage(self, index: int, total_images: int) -> str:
        """Determine the usage type for an image based on its position"""
        if index == 0:
            return "featured"
        elif index < 4:
            return "supporting"
        else:
            return "supplementary"
    
    def _get_recommended_size(self, usage_type: str) -> Dict[str, int]:
        """Get recommended dimensions based on usage type"""
        size_map = {
            "featured": {"width": 1200, "height": 630, "description": "Social media optimized"},
            "supporting": {"width": 800, "height": 450, "description": "In-content image"},
            "supplementary": {"width": 600, "height": 400, "description": "Secondary content"}
        }
        return size_map.get(usage_type, size_map["supporting"])
    
    def _generate_alt_text(self, description: str, topic: str, usage_type: str) -> str:
        """Generate SEO-friendly alt text for images"""
        if description and description.strip():
            base_alt = description.strip()
        else:
            base_alt = f"Professional image related to {topic}"
        
        # Enhance alt text based on usage
        if usage_type == "featured":
            return f"{base_alt} - Featured image for {topic} blog post"
        else:
            return f"{base_alt} - Illustrating {topic} concepts"
    
    def _generate_filename(self, topic: str, image_id: str, usage_type: str) -> str:
        """Generate SEO-friendly filename"""
        # Clean topic for filename
        clean_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).rstrip()
        clean_topic = clean_topic.replace(' ', '-').lower()
        
        return f"{clean_topic}-{usage_type}-{image_id}.jpg"
    
    def _select_optimal_url(self, urls: Dict[str, str], usage_type: str) -> str:
        """Select the best image URL based on usage type"""
        if usage_type == "featured":
            # Prefer highest quality for featured images
            return urls.get('full', urls.get('large', urls.get('regular', urls.get('medium', ''))))
        else:
            # Use medium quality for supporting images
            return urls.get('regular', urls.get('medium', urls.get('large', '')))
    
    def _suggest_placement(self, usage_type: str, index: int) -> str:
        """Suggest where to place the image in the blog"""
        if usage_type == "featured":
            return "Blog header/top of post"
        elif index == 1:
            return "After introduction section"
        elif index == 2:
            return "Middle of main content"
        else:
            return f"Section {index} or conclusion"
    
    def _extract_seo_keywords(self, topic: str, description: str) -> List[str]:
        """Extract SEO keywords from topic and description"""
        keywords = []
        
        # Add topic-related keywords
        topic_words = [word.strip().lower() for word in topic.split() if len(word) > 2]
        keywords.extend(topic_words)
        
        # Extract from description
        if description:
            desc_words = [word.strip().lower() for word in description.split() if len(word) > 3]
            keywords.extend(desc_words[:3])  # Limit to top 3 descriptive words
        
        # Remove duplicates and return
        return list(set(keywords))[:5]  # Limit to 5 keywords
    
    def _generate_caption(self, description: str, topic: str) -> str:
        """Generate a caption for the image"""
        if description and len(description.strip()) > 10:
            return f"{description.strip()}"
        else:
            return f"Visual representation of {topic} concepts"
    
    def _generate_attribution_block(self, optimized_images: List[Dict]) -> str:
        """Generate a complete attribution block for all images"""
        attributions = []
        
        for img in optimized_images:
            if img.get('attribution'):
                attributions.append(f"- {img['attribution']}")
        
        if attributions:
            return "Image Credits:\n" + "\n".join(attributions)
        else:
            return "Images used under appropriate licensing terms."
    
    def _generate_seo_summary(self, optimized_images: List[Dict]) -> Dict[str, Any]:
        """Generate SEO summary for the image collection"""
        total_keywords = []
        total_alt_text = []
        
        for img in optimized_images:
            if img.get('seo_keywords'):
                total_keywords.extend(img['seo_keywords'])
            if img.get('alt_text'):
                total_alt_text.append(img['alt_text'])
        
        return {
            'total_images': len(optimized_images),
            'unique_keywords': len(set(total_keywords)),
            'avg_alt_text_length': sum(len(alt) for alt in total_alt_text) // len(total_alt_text) if total_alt_text else 0,
            'seo_compliance': 'good' if len(total_alt_text) == len(optimized_images) else 'needs_improvement'
        }