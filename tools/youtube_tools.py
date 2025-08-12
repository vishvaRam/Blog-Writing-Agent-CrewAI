"""
YouTube Tools for CrewAI Blog Automation
Optimized implementation with chunking and summarization to reduce LLM context usage
Falls back to video description when transcripts are unavailable
"""

import os
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import Counter
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
    name: str = "YouTube Transcript Extractor with Summarization"
    description: str = "Extract and summarize transcript from a YouTube video to optimize for LLM context length"
    
    def _run(self, video_id: str, video_description: str = "", language_preference: str = 'en', max_summary_length: int = 1000) -> str:
        """
        Extract and summarize transcript from a YouTube video
        
        Args:
            video_id: YouTube video ID
            video_description: Video description as fallback if transcript unavailable
            language_preference: Preferred language code (default: 'en')
            max_summary_length: Maximum length for summary to control context size
        
        Returns:
            JSON string with summarized transcript data and key insights
        """
        try:
            try:
                # Initialize YouTubeTranscriptApi and get transcript list
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
                    'key_insights': self._extract_insights_from_description(video_description),
                    'summary': video_description[:max_summary_length] if video_description else "(No content available)",
                    'word_count': len(video_description.split()) if video_description else 0,
                    'topics': [],
                    'quotes': [],
                    'quality_metrics': {
                        'quality_score': 50 if video_description else 0,
                        'issues': ['Transcript not available'],
                        'recommended_for_blog': bool(video_description)
                    },
                    'extraction_timestamp': datetime.now().isoformat(),
                    'fallback_used': True
                })
            
            # Process and summarize transcript data
            processed_data = self._process_and_summarize_transcript(transcript_data, max_summary_length)
            quality_metrics = self._assess_transcript_quality(transcript_data)
            
            return json.dumps({
                'video_id': video_id,
                'language': transcript.language_code,
                'source_type': source_type,
                'key_insights': processed_data['key_insights'],
                'summary': processed_data['summary'],
                'topics': processed_data['topics'],
                'quotes': processed_data['quotes'],
                'statistics': processed_data['statistics'],
                'word_count': processed_data['original_word_count'],
                'summary_word_count': processed_data['summary_word_count'],
                'duration_seconds': processed_data['duration'],
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
                'summary': video_description[:max_summary_length] if video_description else "(Error occurred and no content available)",
                'key_insights': [],
                'word_count': len(video_description.split()) if video_description else 0,
                'fallback_used': True,
                'extraction_timestamp': datetime.now().isoformat()
            })
    
    def _process_and_summarize_transcript(self, transcript_data: List[Dict], max_length: int = 1000) -> Dict[str, Any]:
        """Process transcript and extract key insights instead of full text"""
        full_text = ' '.join([item['text'] for item in transcript_data])
        word_count = len(full_text.split())
        duration = transcript_data[-1]['start'] + transcript_data[-1]['duration'] if transcript_data else 0
        
        # Clean up the text
        full_text = re.sub(r'\[.*?\]', '', full_text)  # Remove timestamps and annotations
        full_text = re.sub(r'\s+', ' ', full_text).strip()  # Normalize whitespace
        
        # Extract key components
        key_insights = self._extract_key_insights(full_text)
        topics = self._extract_topics(full_text)
        quotes = self._extract_important_quotes(full_text)
        statistics = self._extract_statistics(full_text)
        
        # Create a concise summary
        summary = self._create_summary(full_text, max_length)
        
        return {
            'key_insights': key_insights,
            'summary': summary,
            'topics': topics,
            'quotes': quotes,
            'statistics': statistics,
            'original_word_count': word_count,
            'summary_word_count': len(summary.split()),
            'duration': duration
        }
    
    def _extract_key_insights(self, text: str) -> List[str]:
        """Extract key insights and main points from transcript"""
        insights = []
        
        # Look for sentences with key insight indicators
        sentences = re.split(r'[.!?]+', text)
        insight_keywords = [
            'important', 'key', 'crucial', 'essential', 'main point',
            'remember', 'tip', 'advice', 'recommendation', 'secret',
            'mistake', 'avoid', 'best practice', 'lesson', 'takeaway'
        ]
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20:  # Avoid very short sentences
                for keyword in insight_keywords:
                    if keyword in sentence.lower():
                        insights.append(sentence[:200] + '...' if len(sentence) > 200 else sentence)
                        break
        
        # Return top 5 insights
        return insights[:5]
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract main topics using keyword analysis"""
        # Remove common words and extract meaningful terms
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        common_words = {
            'that', 'this', 'with', 'have', 'will', 'been', 'were', 'said', 
            'what', 'your', 'they', 'them', 'like', 'just', 'know', 'think',
            'really', 'going', 'want', 'need', 'make', 'time', 'people'
        }
        meaningful_words = [word for word in words if word not in common_words]
        
        # Get most frequent terms
        word_counts = Counter(meaningful_words)
        return [word for word, count in word_counts.most_common(10)]
    
    def _extract_important_quotes(self, text: str) -> List[str]:
        """Extract important quotes or statements"""
        quotes = []
        
        # Look for quoted text or emphatic statements
        sentences = re.split(r'[.!?]+', text)
        quote_indicators = [
            '"', "'", 'i believe', 'i think', 'in my opinion',
            'the key is', 'what matters', 'most important'
        ]
        
        for sentence in sentences:
            sentence = sentence.strip()
            if 30 <= len(sentence) <= 150:  # Good quote length
                for indicator in quote_indicators:
                    if indicator in sentence.lower():
                        quotes.append(sentence)
                        break
        
        return quotes[:3]  # Top 3 quotes
    
    def _extract_statistics(self, text: str) -> List[str]:
        """Extract statistics and numerical data"""
        statistics = []
        
        # Look for patterns with numbers and percentages
        stat_patterns = [
            r'\d+\s*percent',
            r'\d+%',
            r'\$\d+[\d,]*',
            r'\d+\s*million',
            r'\d+\s*billion',
            r'\d+\s*times',
            r'\d+\s*years?',
            r'\d+\s*months?'
        ]
        
        for pattern in stat_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Get surrounding context
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end].strip()
                statistics.append(context)
        
        return list(set(statistics))[:5]  # Remove duplicates, top 5
    
    def _create_summary(self, text: str, max_length: int) -> str:
        """Create a concise summary of the transcript"""
        sentences = re.split(r'[.!?]+', text)
        
        # Score sentences based on position and content
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if len(sentence) < 20:
                continue
                
            score = 0
            
            # Position scoring (beginning and end are important)
            if i < len(sentences) * 0.2:  # First 20%
                score += 2
            elif i > len(sentences) * 0.8:  # Last 20%
                score += 1
            
            # Content scoring
            important_words = ['important', 'key', 'main', 'summary', 'conclusion']
            for word in important_words:
                if word in sentence.lower():
                    score += 1
            
            scored_sentences.append((score, sentence))
        
        # Sort by score and select top sentences
        scored_sentences.sort(reverse=True)
        
        summary_sentences = []
        current_length = 0
        
        for score, sentence in scored_sentences:
            if current_length + len(sentence) <= max_length:
                summary_sentences.append(sentence)
                current_length += len(sentence)
            else:
                break
        
        return ' '.join(summary_sentences)
    
    def _extract_insights_from_description(self, description: str) -> List[str]:
        """Extract insights from video description as fallback"""
        if not description:
            return []
        
        # Split by lines and extract meaningful lines
        lines = description.split('\n')
        insights = []
        
        for line in lines:
            line = line.strip()
            if 20 <= len(line) <= 200 and not line.startswith('http'):
                insights.append(line)
        
        return insights[:5]
    
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
            issues.append('Very long transcript - using summarization')
            # Don't penalize for long transcripts since we're summarizing
        
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
