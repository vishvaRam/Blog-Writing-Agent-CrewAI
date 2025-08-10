"""
CrewAI YouTube Blog Automation System
Main crew configuration using Google Gemini LLM and stock images
"""

import os
from pathlib import Path
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv

# Import custom tools
from tools.youtube_tools import YouTubeSearchTool, YouTubeTranscriptTool
from tools.content_tools import ContentStructuringTool, SEOOptimizationTool
from tools.stock_image_tools import PexelsSearchTool, ImageOptimizerTool
from tools.publishing_tools import MediumPublisherTool, ContentFormatterTool, PublicationTrackerTool

# Load environment variables
load_dotenv()


@CrewBase
class YouTubeBlogCrew:
    """YouTube Blog Automation Crew with Gemini LLM and Stock Images"""
    
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    
    def __init__(self):
        """Initialize the crew with Gemini LLM configurations"""
        
        # Validate required environment variables
        required_vars = [
            'GEMINI_API_KEY',
            'YOUTUBE_API_KEY',
            'MEDIUM_INTEGRATION_TOKEN',
            'UNSPLASH_ACCESS_KEY',
            'PEXELS_API_KEY'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Configure Gemini LLM instances
        self.gemini_flash = LLM(
            model="gemini/gemini-2.5-flash",
            api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0.7
        )
        
        self.gemini_pro = LLM(
            model="gemini/gemini-2.5-flash",
            api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0.8
        )
        
        # Create output directories
        self._create_output_directories()
    
    def _create_output_directories(self):
        """Create necessary output directories"""
        directories = [
            'output/research',
            'output/content', 
            'output/images',
            'output/published'
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    @agent
    def youtube_researcher(self) -> Agent:
        """Create YouTube content researcher agent"""
        return Agent(
            role="YouTube Content Researcher and Transcript Extractor",
            goal="Find and extract high-quality transcripts from the top 3 most recent YouTube videos related to the specified topic",
            backstory="""You are an expert digital researcher with deep knowledge of YouTube's content 
            ecosystem and video analysis. You excel at finding the most relevant and recent videos on any given topic, 
            evaluating their quality, and extracting meaningful insights from their transcripts. You understand what 
            makes content valuable for blog creation and can identify key themes and insights across multiple sources.""",
            tools=[
                YouTubeSearchTool(),
                YouTubeTranscriptTool(),
            ],
            llm=self.gemini_flash,
            verbose=True,
            allow_delegation=False,
            max_iter=3,
            memory=True
        )
    
    @agent  
    def content_writer(self) -> Agent:
        """Create AI blog content writer agent"""
        return Agent(
            role="AI Blog Content Writer and SEO Specialist",
            goal="Transform video transcripts into engaging, well-structured blog posts with 6-10 minute read time that provide genuine value to readers",
            backstory="""You are a skilled content writer with expertise in creating engaging long-form blog content 
            that ranks well on search engines. You understand how to structure information for maximum reader engagement, 
            synthesize insights from multiple sources, and create compelling narratives. Your writing style is conversational 
            yet authoritative, making complex topics accessible to a broad audience. You excel at SEO optimization while 
            maintaining natural, human-like writing quality.""",
            tools=[
                ContentStructuringTool(),
                SEOOptimizationTool(),
            ],
            llm=self.gemini_pro,  # Using Pro model for better writing quality
            verbose=True,
            allow_delegation=False,
            max_iter=3,
            memory=True
        )
    
    @agent
    def image_curator(self) -> Agent:
        """Create stock image curator agent"""
        return Agent(
            role="Stock Image Curator and Visual Content Specialist",
            goal="Search and select high-quality, relevant stock images that enhance the blog post content and improve reader engagement",
            backstory="""You are a visual content expert with an eye for compelling imagery and deep understanding 
            of how visuals enhance digital content. You excel at finding high-quality stock photos that perfectly 
            complement written content and enhance the overall user experience. You understand the importance of 
            visual storytelling, proper image attribution, and SEO optimization for images. Your selections always 
            consider the target audience and content context.""",
            tools=[
                # UnsplashSearchTool(),
                PexelsSearchTool(),
                ImageOptimizerTool(),
            ],
            llm=self.gemini_flash,
            verbose=True,
            allow_delegation=False,
            max_iter=2,
            memory=True
        )
    
    @agent
    def content_publisher(self) -> Agent:
        """Create content publisher agent"""
        return Agent(
            role="Multi-Platform Content Publishing Specialist",
            goal="Automatically format and publish completed blog posts to Medium and other platforms with proper formatting and metadata",
            backstory="""You are a publishing automation expert who ensures content reaches its intended audience 
            through proper formatting, strategic timing, and platform optimization. You handle all technical aspects 
            of content distribution, from formatting and metadata configuration to publication scheduling and performance 
            tracking. Your expertise ensures content is properly optimized for each platform's algorithms and best practices.""",
            tools=[
                MediumPublisherTool(),
                ContentFormatterTool(),
                PublicationTrackerTool(),
            ],
            llm=self.gemini_flash,
            verbose=True,
            allow_delegation=False,
            max_iter=2,
            memory=True
        )
    
    @task
    def research_videos_task(self) -> Task:
        """Create video research task"""
        return Task(
            description="""Research and find the top 3 most recent, high-quality YouTube videos related to the topic: {topic}.
            
            Detailed Steps:
            1. Use YouTube Data API to search for recent videos on the specified topic
            2. Filter results by upload date (prioritize videos from last 7-30 days)
            3. Evaluate videos based on relevance, duration (prefer 10+ minutes), channel credibility, and engagement
            4. Select the top 3 videos that best match the criteria
            5. Extract full transcripts from each selected video using YouTube Transcript API
            6. Analyze transcript quality and content depth
            7. Identify key themes, insights, and unique perspectives from each video
            8. Compile comprehensive research findings in structured format
            
            Quality Requirements:
            - Videos must have clear, substantial transcripts
            - Prefer videos with good audio quality and minimal background noise
            - Ensure diversity of perspectives across the 3 selected videos
            - Verify transcripts contain actionable insights and valuable information""",
            
            expected_output="""A comprehensive research report in Markdown format containing:
            - Executive summary of findings for the topic
            - Detailed information for each of the 3 videos (title, URL, upload date, duration, channel info)
            - Full transcripts with timestamps
            - Content quality assessment and relevance scores
            - Key insights and main themes identified
            - Cross-video analysis identifying common themes and contrasting viewpoints
            - Recommendations for primary focus areas for the blog post
            - Source credibility assessment for each video""",
            
            agent=self.youtube_researcher(),
            output_file="output/research/video_research_{topic}.md"
        )
    
    @task
    def write_blog_post_task(self) -> Task:
        """Create blog writing task"""
        return Task(
            description="""Create a comprehensive, engaging blog post based on the video research data.
            Target 6-10 minute read time (approximately 1,500-2,500 words) with high-quality, valuable content.
            
            Content Requirements:
            - Write in an engaging, conversational tone that builds authority
            - Target read time: 6-10 minutes (1,500-2,500 words)
            - Integrate insights from all 3 researched videos seamlessly
            - Create original content that adds value beyond the source material
            - Include compelling examples, explanations, and actionable insights
            - Maintain logical flow and strong narrative structure
            - Optimize for SEO with natural keyword integration
            - Include engaging hooks, transitions, and a strong conclusion
            
            Structure Requirements:
            - Compelling, SEO-optimized title (50-60 characters)
            - Engaging meta description (150-160 characters)
            - Strong introduction with hook and clear value proposition
            - 4-6 main sections with descriptive H2 headings
            - 2-3 subsections per main section with H3 headings
            - Conclusion with key takeaways and call-to-action
            - Proper attribution and references to source videos""",
            
            expected_output="""A complete, publication-ready blog post in Markdown format including:
            - SEO-optimized title and meta description
            - Well-structured content with proper heading hierarchy
            - 1,500-2,500 word count with engaging, valuable content
            - Natural integration of insights from all source videos
            - Compelling introduction that hooks readers immediately
            - Logical section progression with smooth transitions
            - Strong conclusion with clear takeaways and next steps
            - Proper citations and attribution to source videos
            - Suggestions for image placement throughout the content""",
            
            agent=self.content_writer(),
            context=[self.research_videos_task()],
            output_file="output/content/blog_post_{topic}.md"
        )
    
    @task
    def curate_images_task(self) -> Task:
        """Create image curation task"""
        return Task(
            description="""Search for and curate high-quality stock images to enhance the blog post content.
            Focus on finding professional, relevant imagery that supports the written content and improves reader engagement.
            
            Image Requirements:
            - Search for 1 featured image for the blog post header/social sharing
            - Find 3-4 supporting images for main content sections
            - Ensure all images are relevant to the topic and specific content sections
            - Select high-resolution, professional-quality photographs
            - Verify proper licensing for commercial/editorial use
            - Maintain visual consistency and professional appearance
            
            Technical Specifications:
            - Featured image: High resolution, social media optimized (1200x630px preferred)
            - Supporting images: Web-optimized resolution (800x450px recommended)
            - Professional stock photography preferred over illustrations
            - SEO optimization with descriptive alt text and file names
            - Proper attribution for photographers and sources""",
            
            expected_output="""A curated collection of stock images with complete metadata:
            - 1 high-quality featured image with social media optimization
            - 3-4 supporting images aligned with specific content sections
            - Comprehensive image metadata including URLs, alt text, file names, attribution
            - Photographer attribution and source information
            - Licensing and usage rights details
            - Recommended placement within blog content
            - Image dimensions and technical specifications
            - Visual style consistency report""",
            
            agent=self.image_curator(),
            context=[self.write_blog_post_task()],
            output_file="output/images/image_collection_{topic}.json"
        )
    
    @task  
    def publish_content_task(self) -> Task:
        """Create content publishing task"""
        return Task(
            description="""Format and publish the completed blog post with images to the Medium platform.
            Ensure proper formatting, metadata configuration, and optimal presentation for maximum reader engagement.
            
            Publishing Requirements:
            - Format content according to Medium's best practices and guidelines
            - Configure appropriate tags, categories, and publication settings
            - Set up proper SEO metadata including title, description, and canonical URLs
            - Ensure all formatting and media elements work correctly
            - Schedule publication for optimal timing or publish immediately
            
            Content Formatting:
            - Convert Markdown to Medium-compatible rich text formatting
            - Ensure proper heading hierarchy and text formatting
            - Add proper image attributions for stock images
            - Format citations and references appropriately
            
            Quality Assurance:
            - Verify all images display correctly and load quickly
            - Check all links and references work properly
            - Ensure proper formatting across different devices
            - Confirm all attribution and licensing requirements are met""",
            
            expected_output="""Comprehensive publication report including:
            - Medium post URL and publication confirmation
            - Publication timestamp and scheduling details
            - Configured metadata (title, tags, description, etc.)
            - SEO configuration summary
            - Performance tracking setup details
            - Publication success/failure status with details
            - Post-publication checklist completion status
            - Engagement and analytics setup confirmation
            - Any errors or issues encountered during publishing""",
            
            agent=self.content_publisher(),
            context=[self.write_blog_post_task(), self.curate_images_task()],
            output_file="output/published/publication_report_{topic}.json"
        )
    
    @crew
    def crew(self) -> Crew:
        """Create the YouTube Blog automation crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks, 
            process=Process.sequential,
            verbose=True,
            memory=True,
            embedder={
                "provider": "google",  # Using Google embeddings for consistency
                "config": {
                    "model": "models/embedding-001",
                    "api_key": os.getenv("GEMINI_API_KEY")
                }
            },
            max_rpm=10,  # Rate limiting to respect API limits
            language="en"
        )