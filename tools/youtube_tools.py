"""
YouTube Tools for CrewAI Blog Automation
Contains tools for searching YouTube videos and extracting transcripts
"""

import os
import json
from pydantic import Field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from crewai.tools import BaseTool
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import re


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
            JSON string with video information
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
                order='relevance',  # Changed from 'date' to get more relevant content
                maxResults=min(max_results, 50),
                publishedAfter=published_after,
                videoDuration='medium',  # Filter for videos 4-20 minutes
                videoDefinition='high',  # Prefer HD videos
                safeSearch='moderate'
            ).execute()
            
            videos = []
            video_ids = [item['id']['videoId'] for item in search_response['items']]
            
            # Get additional video details
            videos_response = self.youtube.videos().list(
                part='snippet,statistics,contentDetails',
                id=','.join(video_ids)
            ).execute()
            
            for item in videos_response['items']:
                # Parse duration
                duration = self._parse_duration(item['contentDetails']['duration'])
                
                # Filter for videos with substantial content (at least 5 minutes)
                if duration < 300:  # Skip videos shorter than 5 minutes
                    continue
                
                video_data = {
                    'video_id': item['id'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'][:500] + '...' if len(item['snippet']['description']) > 500 else item['snippet']['description'],
                    'published_at': item['snippet']['publishedAt'],
                    'channel_title': item['snippet']['channelTitle'],
                    'channel_id': item['snippet']['channelId'],
                    'duration_seconds': duration,
                    'duration_formatted': self._format_duration(duration),
                    'view_count': int(item['statistics'].get('viewCount', 0)),
                    'like_count': int(item['statistics'].get('likeCount', 0)),
                    'comment_count': int(item['statistics'].get('commentCount', 0)),
                    'thumbnail_url': item['snippet']['thumbnails']['high']['url'],
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
            score += min(20, view_count / 50000)  # Cap at 20 points
        
        # Engagement rate (20% weight)
        likes = int(video_item['statistics'].get('likeCount', 0))
        comments = int(video_item['statistics'].get('commentCount', 0))
        if view_count > 0:
            engagement_rate = (likes + comments * 2) / view_count
            score += min(20, engagement_rate * 1000000)  # Normalize and cap
        
        # Duration preference (10% weight) - prefer 10-30 minute videos
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
    description: str = "Extract transcript from a YouTube video with error handling and quality assessment"
    
    def _run(self, video_id: str, language_preference: str = 'en') -> str:
        """
        Extract transcript from a YouTube video
        
        Args:
            video_id: YouTube video ID
            language_preference: Preferred language code (default: 'en')
        
        Returns:
            JSON string with transcript data or error information
        """
        try:
            # Try to get transcript in preferred language first
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                
                # Try to find transcript in preferred language
                try:
                    transcript = transcript_list.find_transcript([language_preference])
                    transcript_data = transcript.fetch()
                    source_type = "manual" if not transcript.is_generated else "auto-generated"
                except:
                    # Fall back to any available transcript
                    transcript = transcript_list.find_generated_transcript(['en', 'en-US', 'en-GB'])
                    transcript_data = transcript.fetch()
                    source_type = "auto-generated"
                    
            except (TranscriptsDisabled, NoTranscriptFound):
                return json.dumps({
                    'error': 'No transcript available for this video',
                    'video_id': video_id,
                    'available_transcripts': []
                })
            
            # Process transcript data
            processed_transcript = self._process_transcript(transcript_data)
            
            # Calculate quality metrics
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
                'extraction_timestamp': datetime.now().isoformat()
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                'error': f"Error extracting transcript: {str(e)}",
                'video_id': video_id
            })
    
    def _process_transcript(self, transcript_data: List[Dict]) -> Dict[str, Any]:
        """Process raw transcript data into usable format"""
        full_text = ' '.join([item['text'] for item in transcript_data])
        word_count = len(full_text.split())
        duration = transcript_data[-1]['start'] + transcript_data[-1]['duration'] if transcript_data else 0
        
        # Clean up the text
        full_text = re.sub(r'\[.*?\]', '', full_text)  # Remove time stamps and annotations
        full_text = re.sub(r'\s+', ' ', full_text).strip()  # Normalize whitespace
        
        return {
            'full_text': full_text,
            'word_count': word_count,
            'duration': duration
        }
    
    def _assess_transcript_quality(self, transcript_data: List[Dict]) -> Dict[str, Any]:
        """Assess the quality of the transcript for blog creation"""
        if not transcript_data:
            return {'quality_score': 0, 'issues': ['No transcript data']}
        
        issues = []
        quality_score = 100
        
        # Check for very short segments (indicates poor audio quality)
        short_segments = sum(1 for item in transcript_data if len(item['text']) < 10)
        if short_segments > len(transcript_data) * 0.3:
            issues.append('Many short transcript segments detected')
            quality_score -= 20
        
        # Check for repeated phrases (common in auto-generated transcripts)
        text = ' '.join([item['text'] for item in transcript_data])
        words = text.lower().split()
        if len(set(words)) < len(words) * 0.3:  # Less than 30% unique words
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
        error_count = sum(text.lower().count(indicator) for indicator in error_indicators)
        if error_count > 20:
            issues.append('High number of transcript errors detected')
            quality_score -= 10
        
        return {
            'quality_score': max(0, quality_score),
            'word_count': word_count,
            'segment_count': len(transcript_data),
            'issues': issues,
            'recommended_for_blog': quality_score >= 70
        }