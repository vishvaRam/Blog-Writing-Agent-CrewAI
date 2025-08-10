"""
Configuration Manager for YouTube Blog Automation System
Handles configuration loading, validation, and management
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class APIConfig:
    """API configuration data class"""
    name: str
    api_key: str
    base_url: str = ""
    rate_limit: int = 60
    timeout: int = 30


@dataclass
class ContentConfig:
    """Content generation configuration"""
    target_read_time: int = 8
    min_word_count: int = 1500
    max_word_count: int = 2500
    max_videos_per_topic: int = 3
    image_count: int = 4
    seo_keywords_count: int = 5


@dataclass
class PublishingConfig:
    """Publishing configuration"""
    default_platform: str = "medium"
    publish_status: str = "draft"  # draft, public, unlisted
    auto_publish: bool = False
    schedule_delay_hours: int = 0


class ConfigManager:
    """Manage application configuration and settings"""
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize configuration manager
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        # Load environment variables
        load_dotenv()
        
        # Initialize configurations
        self.api_configs = self._load_api_configs()
        self.content_config = self._load_content_config()
        self.publishing_config = self._load_publishing_config()
        
        # Validate configurations
        self._validate_configurations()
    
    def _load_api_configs(self) -> Dict[str, APIConfig]:
        """Load API configurations"""
        
        api_configs = {}
        
        # YouTube Data API
        if os.getenv('YOUTUBE_API_KEY'):
            api_configs['youtube'] = APIConfig(
                name="YouTube Data API",
                api_key=os.getenv('YOUTUBE_API_KEY'),
                base_url="https://www.googleapis.com/youtube/v3",
                rate_limit=10000,  # 10,000 units per day
                timeout=30
            )
        
        # Google Gemini API
        if os.getenv('GEMINI_API_KEY'):
            api_configs['gemini'] = APIConfig(
                name="Google Gemini API",
                api_key=os.getenv('GEMINI_API_KEY'),
                base_url="https://generativelanguage.googleapis.com/v1beta",
                rate_limit=60,  # Requests per minute
                timeout=60
            )
        
        # Medium API
        if os.getenv('MEDIUM_INTEGRATION_TOKEN'):
            api_configs['medium'] = APIConfig(
                name="Medium API",
                api_key=os.getenv('MEDIUM_INTEGRATION_TOKEN'),
                base_url="https://api.medium.com/v1",
                rate_limit=15,  # 15 posts per day
                timeout=30
            )
        
        # Unsplash API
        if os.getenv('UNSPLASH_ACCESS_KEY'):
            api_configs['unsplash'] = APIConfig(
                name="Unsplash API",
                api_key=os.getenv('UNSPLASH_ACCESS_KEY'),
                base_url="https://api.unsplash.com",
                rate_limit=5000,  # 5000 requests per hour
                timeout=15
            )
        
        # Pexels API
        if os.getenv('PEXELS_API_KEY'):
            api_configs['pexels'] = APIConfig(
                name="Pexels API",
                api_key=os.getenv('PEXELS_API_KEY'),
                base_url="https://api.pexels.com/v1",
                rate_limit=200,  # 200 requests per hour
                timeout=15
            )
        
        return api_configs
    
    def _load_content_config(self) -> ContentConfig:
        """Load content generation configuration"""
        
        return ContentConfig(
            target_read_time=int(os.getenv('TARGET_READ_TIME', 8)),
            min_word_count=int(os.getenv('MIN_WORD_COUNT', 1500)),
            max_word_count=int(os.getenv('MAX_WORD_COUNT', 2500)),
            max_videos_per_topic=int(os.getenv('MAX_VIDEOS_PER_TOPIC', 3)),
            image_count=int(os.getenv('IMAGE_COUNT', 4)),
            seo_keywords_count=int(os.getenv('SEO_KEYWORDS_COUNT', 5))
        )
    
    def _load_publishing_config(self) -> PublishingConfig:
        """Load publishing configuration"""
        
        return PublishingConfig(
            default_platform=os.getenv('DEFAULT_PLATFORM', 'medium'),
            publish_status=os.getenv('PUBLISH_STATUS', 'draft'),
            auto_publish=os.getenv('AUTO_PUBLISH', 'false').lower() == 'true',
            schedule_delay_hours=int(os.getenv('SCHEDULE_DELAY_HOURS', 0))
        )
    
    def _validate_configurations(self):
        """Validate all configurations"""
        
        required_apis = ['youtube', 'gemini', 'medium', 'unsplash', 'pexels']
        missing_apis = []
        
        for api_name in required_apis:
            if api_name not in self.api_configs:
                missing_apis.append(api_name)
        
        if missing_apis:
            raise ValueError(f"Missing required API configurations: {', '.join(missing_apis)}")
        
        # Validate content configuration
        if self.content_config.min_word_count >= self.content_config.max_word_count:
            raise ValueError("min_word_count must be less than max_word_count")
        
        if self.content_config.target_read_time < 3:
            raise ValueError("target_read_time must be at least 3 minutes")
        
        # Validate publishing configuration
        valid_platforms = ['medium', 'wordpress', 'ghost', 'dev.to']
        if self.publishing_config.default_platform not in valid_platforms:
            raise ValueError(f"default_platform must be one of: {', '.join(valid_platforms)}")
        
        valid_statuses = ['draft', 'public', 'unlisted']
        if self.publishing_config.publish_status not in valid_statuses:
            raise ValueError(f"publish_status must be one of: {', '.join(valid_statuses)}")
    
    def get_api_config(self, api_name: str) -> Optional[APIConfig]:
        """Get API configuration by name"""
        return self.api_configs.get(api_name)
    
    def get_all_api_configs(self) -> Dict[str, APIConfig]:
        """Get all API configurations"""
        return self.api_configs.copy()
    
    def get_content_config(self) -> ContentConfig:
        """Get content generation configuration"""
        return self.content_config
    
    def get_publishing_config(self) -> PublishingConfig:
        """Get publishing configuration"""
        return self.publishing_config
    
    def update_content_config(self, **kwargs):
        """Update content configuration"""
        
        for key, value in kwargs.items():
            if hasattr(self.content_config, key):
                setattr(self.content_config, key, value)
        
        # Re-validate after update
        self._validate_configurations()
    
    def update_publishing_config(self, **kwargs):
        """Update publishing configuration"""
        
        for key, value in kwargs.items():
            if hasattr(self.publishing_config, key):
                setattr(self.publishing_config, key, value)
        
        # Re-validate after update
        self._validate_configurations()
    
    def save_config_to_file(self, filename: str = "app_config.json"):
        """Save current configuration to file"""
        
        config_data = {
            'content_config': {
                'target_read_time': self.content_config.target_read_time,
                'min_word_count': self.content_config.min_word_count,
                'max_word_count': self.content_config.max_word_count,
                'max_videos_per_topic': self.content_config.max_videos_per_topic,
                'image_count': self.content_config.image_count,
                'seo_keywords_count': self.content_config.seo_keywords_count
            },
            'publishing_config': {
                'default_platform': self.publishing_config.default_platform,
                'publish_status': self.publishing_config.publish_status,
                'auto_publish': self.publishing_config.auto_publish,
                'schedule_delay_hours': self.publishing_config.schedule_delay_hours
            },
            'api_services': list(self.api_configs.keys())
        }
        
        config_file = self.config_dir / filename
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def load_config_from_file(self, filename: str = "app_config.json"):
        """Load configuration from file"""
        
        config_file = self.config_dir / filename
        
        if not config_file.exists():
            return
        
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        
        # Update content configuration
        if 'content_config' in config_data:
            self.update_content_config(**config_data['content_config'])
        
        # Update publishing configuration
        if 'publishing_config' in config_data:
            self.update_publishing_config(**config_data['publishing_config'])
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get a summary of all configurations"""
        
        return {
            'api_services': {
                name: {
                    'name': config.name,
                    'configured': bool(config.api_key),
                    'base_url': config.base_url,
                    'rate_limit': config.rate_limit
                }
                for name, config in self.api_configs.items()
            },
            'content_settings': {
                'target_read_time_minutes': self.content_config.target_read_time,
                'word_count_range': f"{self.content_config.min_word_count}-{self.content_config.max_word_count}",
                'max_videos_per_topic': self.content_config.max_videos_per_topic,
                'images_per_post': self.content_config.image_count
            },
            'publishing_settings': {
                'default_platform': self.publishing_config.default_platform,
                'default_status': self.publishing_config.publish_status,
                'auto_publish_enabled': self.publishing_config.auto_publish
            }
        }
    
    def validate_topic(self, topic: str) -> bool:
        """Validate if a topic is suitable for content generation"""
        
        if not topic or not topic.strip():
            return False
        
        if len(topic.strip()) < 3:
            return False
        
        # Check for inappropriate content (basic filtering)
        inappropriate_terms = ['adult', 'explicit', 'violence', 'illegal']
        topic_lower = topic.lower()
        
        for term in inappropriate_terms:
            if term in topic_lower:
                return False
        
        return True
    
    def get_recommended_tags(self, topic: str) -> List[str]:
        """Get recommended tags for a topic"""
        
        # This is a simple implementation - could be enhanced with ML/AI
        topic_words = topic.lower().split()
        
        # Common technology and content tags
        common_tags = [
            'technology', 'artificial intelligence', 'programming', 'software',
            'digital transformation', 'innovation', 'future', 'trends',
            'business', 'productivity', 'learning', 'education'
        ]
        
        recommended = []
        
        # Add topic words as tags
        for word in topic_words:
            if len(word) > 3:
                recommended.append(word.title())
        
        # Add related common tags
        for tag in common_tags:
            if any(word in tag.lower() for word in topic_words):
                recommended.append(tag.title())
        
        # Remove duplicates and limit to 5
        recommended = list(dict.fromkeys(recommended))[:5]
        
        return recommended