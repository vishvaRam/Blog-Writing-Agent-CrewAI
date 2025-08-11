"""
YouTube Tools for CrewAI Blog Automation
Updated implementation with youtube-transcript-api v1.2.2
Falls back to video description when transcripts are unavailable
"""

import os
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pydantic import Field
from crewai.tools import BaseTool
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound


class YouTubeSearchTool(BaseTool):
    name: str = "YouTube Video Search"
    description: str = "Search for the latest YouTube videos on a specific topic with quality filtering"
    api_key: Optional[str] = Field(default=None, exclude=True)
    youtube: Optional[Any] = Field(default=None, exclude=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_key = os.getenv('YOUTUBE_API_KEY')
        if not self.api_key:
            raise ValueError("YOUTUBE_API_KEY environment variable is required")
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)
        
    def _run(self, topic: str, max_results: int = 10, days_back: int = 30) -> str:
        """
        Search for YouTube videos on a specific topic
        
        Args:
            topic: Search query/topic
            max_results: Number of videos to return (max 50)
            days_back: How many days back to search for videos
        
        Returns:
            JSON string with video information including descriptions
        """
        try:
            # Calculate date for filtering recent videos
            cutoff_date = datetime.now() - timedelta(days=days_back)
            published_after = cutoff_date.isoformat() + 'Z'
            
            # Search for videos
            search_response = self.youtube.search().list(
                q=topic,
                part='snippet',
                type='video',
                order='relevance',
                maxResults=min(max_results, 50),
                publishedAfter=published_after,
                videoDuration='medium',
                videoDefinition='high',
                safeSearch='moderate'
            ).execute()
            
            videos = []
            video_ids = [item['id']['videoId'] for item in search_response['items']]
            
            if not video_ids:
                return json.dumps({
                    'search_query': topic,
                    'total_found': 0,
                    'search_date': datetime.now().isoformat(),
                    'videos': [],
                    'message': 'No videos found for this topic'
                })
            
            # Get additional video details
            videos_response = self.youtube.videos().list(
                part='snippet,statistics,contentDetails',
                id=','.join(video_ids)
            ).execute()
            
            for item in videos_response['items']:
                # Parse duration
                duration = self._parse_duration(item['contentDetails']['duration'])
                
                # Filter for videos with substantial content (at least 5 minutes)
                if duration < 300:
                    continue
                
                # Get full description (not truncated)
                full_description = item['snippet'].get('description', '')
                
                video_data = {
                    'video_id': item['id'],
                    'title': item['snippet']['title'],
                    'description': full_description,
                    'description_preview': full_description[:500] + '...' if len(full_description) > 500 else full_description,
                    'published_at': item['snippet']['publishedAt'],
                    'channel_title': item['snippet']['channelTitle'],
                    'channel_id': item['snippet']['channelId'],
                    'duration_seconds': duration,
                    'duration_formatted': self._format_duration(duration),
                    'view_count': int(item['statistics'].get('viewCount', 0)),
                    'like_count': int(item['statistics'].get('likeCount', 0)),
                    'comment_count': int(item['statistics'].get('commentCount', 0)),
                    'thumbnail_url': item['snippet']['thumbnails'].get('high', {}).get('url', ''),
                    'video_url': f"https://www.youtube.com/watch?v={item['id']}",
                    'relevance_score': self._calculate_relevance_score(item, topic)
                }
                videos.append(video_data)
            
            # Sort by relevance score
            videos.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            return json.dumps({
                'search_query': topic,
                'total_found': len(videos),
                'search_date': datetime.now().isoformat(),
                'videos': videos
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                'error': f"Error searching YouTube: {str(e)}",
                'search_query': topic
            })
    
    def _parse_duration(self, duration_str: str) -> int:
        """Parse YouTube duration format (PT#M#S) to seconds"""
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
        if not match:
            return 0
        
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        
        return hours * 3600 + minutes * 60 + seconds
    
    def _format_duration(self, seconds: int) -> str:
        """Format seconds to HH:MM:SS or MM:SS"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    def _calculate_relevance_score(self, video_item: Dict, topic: str) -> float:
        """Calculate relevance score for ranking videos"""
        score = 0.0
        
        # Title relevance (40% weight)
        title = video_item['snippet']['title'].lower()
        topic_words = topic.lower().split()
        title_matches = sum(1 for word in topic_words if word in title)
        score += (title_matches / len(topic_words)) * 40
        
        # View count factor (20% weight)
        view_count = int(video_item['statistics'].get('viewCount', 0))
        if view_count > 10000:
            score += min(20, view_count / 50000)
        
        # Engagement rate (20% weight)
        likes = int(video_item['statistics'].get('likeCount', 0))
        comments = int(video_item['statistics'].get('commentCount', 0))
        if view_count > 0:
            engagement_rate = (likes + comments * 2) / view_count
            score += min(20, engagement_rate * 1000000)
        
        # Duration preference (10% weight)
        duration = self._parse_duration(video_item['contentDetails']['duration'])
        if 600 <= duration <= 1800:  # 10-30 minutes
            score += 10
        elif 300 <= duration < 600:  # 5-10 minutes
            score += 7
        elif duration > 1800:  # > 30 minutes
            score += 5
        
        # Recency bonus (10% weight)
        published_date = datetime.fromisoformat(video_item['snippet']['publishedAt'].replace('Z', '+00:00'))
        days_old = (datetime.now().replace(tzinfo=published_date.tzinfo) - published_date).days
        if days_old <= 7:
            score += 10
        elif days_old <= 30:
            score += 5
        
        return score


class YouTubeTranscriptTool(BaseTool):
    name: str = "YouTube Transcript Extractor"
    description: str = "Extract transcript from a YouTube video with error handling and fallback to description"
    
    def _run(self, video_id: str, video_description: str = "", language_preference: str = 'en') -> str:
        """
        Extract transcript from a YouTube video using youtube-transcript-api v1.2.2
        
        Args:
            video_id: YouTube video ID
            video_description: Video description as fallback if transcript unavailable
            language_preference: Preferred language code (default: 'en')
        
        Returns:
            JSON string with transcript data or fallback content
        """
        try:
            try:
                # NEW API: Initialize YouTubeTranscriptApi and get transcript list
                ytt_api = YouTubeTranscriptApi()
                transcript_list = ytt_api.list(video_id)
                
                # Try to find transcript in preferred language
                try:
                    # Find transcript with language preference
                    transcript = transcript_list.find_transcript([language_preference])
                    fetched_transcript = transcript.fetch()
                    source_type = "manual" if not transcript.is_generated else "auto-generated"
                    
                    # Convert FetchedTranscript to raw data
                    transcript_data = fetched_transcript.to_raw_data()
                    
                except:
                    # Fallback to any available English transcript
                    languages = ['en', 'en-US', 'en-GB', 'en-CA', 'en-AU']
                    transcript = transcript_list.find_generated_transcript(languages)
                    fetched_transcript = transcript.fetch()
                    transcript_data = fetched_transcript.to_raw_data()
                    source_type = "auto-generated"
                    
            except (TranscriptsDisabled, NoTranscriptFound, Exception):
                # Fallback: use video description if no transcript available
                return json.dumps({
                    'video_id': video_id,
                    'language': 'n/a',
                    'source_type': 'description-fallback',
                    'transcript_segments': [],
                    'full_text': video_description or "(No transcript or description available)",
                    'word_count': len(video_description.split()) if video_description else 0,
                    'duration_seconds': 0,
                    'quality_metrics': {
                        'quality_score': 50 if video_description else 0,
                        'issues': ['Transcript not available'],
                        'recommended_for_blog': bool(video_description)
                    },
                    'extraction_timestamp': datetime.now().isoformat(),
                    'fallback_used': True
                })
            
            # Process transcript data
            processed_transcript = self._process_transcript(transcript_data)
            quality_metrics = self._assess_transcript_quality(transcript_data)
            
            return json.dumps({
                'video_id': video_id,
                'language': transcript.language_code,
                'source_type': source_type,
                'transcript_segments': transcript_data,
                'full_text': processed_transcript['full_text'],
                'word_count': processed_transcript['word_count'],
                'duration_seconds': processed_transcript['duration'],
                'quality_metrics': quality_metrics,
                'extraction_timestamp': datetime.now().isoformat(),
                'fallback_used': False
            }, indent=2)
            
        except Exception as e:
            # Final fallback on any other error
            return json.dumps({
                'video_id': video_id,
                'source_type': 'error-fallback',
                'error': str(e),
                'full_text': video_description or "(Error occurred and no description available)",
                'word_count': len(video_description.split()) if video_description else 0,
                'fallback_used': True,
                'extraction_timestamp': datetime.now().isoformat()
            })
    
    def _process_transcript(self, transcript_data: List[Dict]) -> Dict[str, Any]:
        """Process raw transcript data into usable format"""
        full_text = ' '.join([item['text'] for item in transcript_data])
        word_count = len(full_text.split())
        duration = transcript_data[-1]['start'] + transcript_data[-1]['duration'] if transcript_data else 0
        
        # Clean up the text
        full_text = re.sub(r'\[.*?\]', '', full_text)  # Remove timestamps and annotations
        full_text = re.sub(r'\s+', ' ', full_text).strip()  # Normalize whitespace
        
        return {
            'full_text': full_text,
            'word_count': word_count,
            'duration': duration
        }
    
    def _assess_transcript_quality(self, transcript_data: List[Dict]) -> Dict[str, Any]:
        """Assess the quality of the transcript for blog creation"""
        if not transcript_data:
            return {'quality_score': 0, 'issues': ['No transcript data'], 'recommended_for_blog': False}
        
        issues = []
        quality_score = 100
        
        # Check for very short segments
        short_segments = sum(1 for item in transcript_data if len(item['text']) < 10)
        if short_segments > len(transcript_data) * 0.3:
            issues.append('Many short transcript segments detected')
            quality_score -= 20
        
        # Check for repeated phrases
        text = ' '.join([item['text'] for item in transcript_data])
        words = text.lower().split()
        if len(set(words)) < len(words) * 0.3:
            issues.append('High repetition detected')
            quality_score -= 15
        
        # Check transcript length
        word_count = len(words)
        if word_count < 500:
            issues.append('Transcript too short for substantial content')
            quality_score -= 25
        elif word_count > 5000:
            issues.append('Very long transcript - may need summarization')
            quality_score -= 5
        
        # Check for common transcript errors
        error_indicators = ['[Music]', '[Applause]', '[Inaudible]', 'um,', 'uh,', '...']
        error_count = sum(text.lower().count(indicator.lower()) for indicator in error_indicators)
        if error_count > 20:
            issues.append('High number of transcript errors detected')
            quality_score -= 10
        
        return {
            'quality_score': max(0, quality_score),
            'word_count': word_count,
            'segment_count': len(transcript_data),
            'issues': issues,
            'recommended_for_blog': quality_score >= 50
        }


# Helper function for research aggregation
def extract_video_content(search_tool, transcript_tool, topic: str, max_videos: int = 3) -> str:
    """
    Complete video research workflow that always returns usable content
    """
    try:
        # Search for videos
        search_result = json.loads(search_tool._run(topic, max_videos))
        
        if 'error' in search_result or not search_result.get('videos'):
            return json.dumps({
                'error': 'No videos found or search failed',
                'topic': topic,
                'videos_processed': []
            })
        
        videos_with_content = []
        
        for video in search_result['videos'][:max_videos]:
            # Extract transcript with description fallback
            transcript_result = json.loads(transcript_tool._run(
                video_id=video['video_id'],
                video_description=video['description']
            ))
            
            # Combine video metadata with transcript/content
            video_content = {
                'video_id': video['video_id'],
                'title': video['title'],
                'description': video['description'],
                'channel': video['channel_title'],
                'url': video['video_url'],
                'published_at': video['published_at'],
                'duration': video['duration_formatted'],
                'view_count': video['view_count'],
                'content_text': transcript_result['full_text'],
                'content_source': transcript_result['source_type'],
                'word_count': transcript_result['word_count'],
                'quality_score': transcript_result.get('quality_metrics', {}).get('quality_score', 0),
                'fallback_used': transcript_result.get('fallback_used', False)
            }
            
            videos_with_content.append(video_content)
        
        return json.dumps({
            'topic': topic,
            'total_videos_found': search_result['total_found'],
            'videos_processed': len(videos_with_content),
            'videos': videos_with_content,
            'research_timestamp': datetime.now().isoformat()
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            'error': f"Research workflow failed: {str(e)}",
            'topic': topic,
            'videos_processed': 0
        })


# Additional utility class for direct API usage (optional)
class YouTubeTranscriptExtractor:
    """
    Simplified wrapper for direct transcript extraction
    Based on the latest youtube-transcript-api v1.2.2
    """
    
    @staticmethod
    def get_transcript(video_id: str, languages: List[str] = None) -> Dict[str, Any]:
        """
        Simple transcript extraction method
        
        Args:
            video_id: YouTube video ID
            languages: List of preferred language codes
            
        Returns:
            Dictionary with transcript data
        """
        if languages is None:
            languages = ['en']
            
        try:
            ytt_api = YouTubeTranscriptApi()
            
            # Get transcript using the new API
            fetched_transcript = ytt_api.fetch(video_id, languages=languages)
            
            return {
                'success': True,
                'video_id': video_id,
                'language': fetched_transcript.language_code,
                'is_generated': fetched_transcript.is_generated,
                'transcript_data': fetched_transcript.to_raw_data(),
                'full_text': ' '.join([item['text'] for item in fetched_transcript.to_raw_data()])
            }
            
        except Exception as e:
            return {
                'success': False,
                'video_id': video_id,
                'error': str(e),
                'transcript_data': []
            }
