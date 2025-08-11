"""
Updated CrewAI configuration to save locally first and publish to free platforms
Replaces Medium with Dev.to and adds local saving capability
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
from tools.free_publishing_tools import LocalBlogSaverTool, DevToPublisherTool, HashnodePublisherTool, PublishingOrchestratorTool

# Load environment variables
load_dotenv()


@CrewBase
class YouTubeBlogCrewFree:
    """YouTube Blog Automation Crew with Local Saving and Free Publishing"""
    
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    
    def __init__(self):
        """Initialize the crew with Gemini LLM configurations and free publishing"""
        
        # Validate required environment variables (reduced requirements)
        required_vars = [
            'GEMINI_API_KEY',
            'YOUTUBE_API_KEY',
            'PEXELS_API_KEY'
        ]
        
        # Optional for free publishing
        optional_vars = [
            'DEVTO_API_KEY',      # For Dev.to publishing
            'HASHNODE_TOKEN'      # For Hashnode publishing
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Warn about optional vars
        missing_optional = [var for var in optional_vars if not os.getenv(var)]
        if missing_optional:
            print(f"⚠️  Optional APIs not configured: {', '.join(missing_optional)}")
            print("   Blog will be saved locally. You can publish manually later.")
        
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
        """Create necessary output directories including local blogs"""
        directories = [
            'output/research',
            'output/content', 
            'output/images',
            'output/published',
            'local_blogs'  # New directory for local blog storage
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
            evaluating their quality, and extracting meaningful insights from their transcripts.""",
            tools=[
                YouTubeSearchTool(),
                YouTubeTranscriptTool(),
            ],
            llm=self.gemini_flash,
            verbose=True,
            allow_delegation=False,
            max_iter=4,
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
            synthesize insights from multiple sources, and create compelling narratives.""",
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
            complement written content and enhance the overall user experience.""",
            tools=[
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
        """Create content publisher agent for free platforms"""
        return Agent(
            role="Free Platform Content Publishing Specialist",
            goal="Save blog posts locally and publish to free platforms like Dev.to and Hashnode with proper formatting and metadata",
            backstory="""You are a publishing automation expert who ensures content is properly saved locally first, 
            then distributed to free publishing platforms. You handle local organization, backup, and automated publishing 
            to developer-friendly platforms like Dev.to and Hashnode.""",
            tools=[
                LocalBlogSaverTool(),
                DevToPublisherTool(),
                HashnodePublisherTool(),
                PublishingOrchestratorTool(),
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
            description="""Research and find the top 4 most recent, high-quality YouTube videos related to the topic: {topic}.
            
            Steps:
            1. Use YouTube Data API to search for recent videos on the specified topic
            2. Filter by relevance, duration (prefer 10+ minutes), and engagement metrics
            3. Extract full transcripts from each selected video
            4. Analyze content quality and identify key insights
            5. Compile comprehensive research findings""",
            
            expected_output="""A comprehensive research report in Markdown format containing:
            - Executive summary of findings
            - Detailed information for each of the 4 videos
            - Full transcripts with analysis
            - Key insights and themes identified
            - Recommendations for blog content focus""",
            
            agent=self.youtube_researcher(),
            output_file="output/research/video_research_{topic}.md"
        )
    
    @task
    def write_blog_post_task(self) -> Task:
        """Create blog writing task"""
        return Task(
            description="""Create a comprehensive, engaging blog post based on the video research data.
            Target 8-12 minute read time (2,500-3,500 words) with high-quality, valuable content.
            
            Requirements:
            - Engaging, conversational tone with authority
            - Integrate insights from all 3 researched videos seamlessly
            - Include compelling examples and actionable insights
            - SEO-optimized with natural keyword integration
            - Strong introduction and conclusion
            - Proper attribution to source videos""",
            
            expected_output="""A complete, publication-ready blog post in Markdown format with:
            - SEO-optimized title and meta description
            - Well-structured content with proper headings
            - 2,500-3,500 word count
            - Engaging introduction and strong conclusion
            - Natural integration of video insights
            - Proper citations and references""",
            
            agent=self.content_writer(),
            context=[self.research_videos_task()],
            output_file="output/content/blog_post_{topic}.md"
        )
    
    @task
    def curate_images_task(self) -> Task:
        """Create image curation task"""
        return Task(
            description="""Search for and curate high-quality stock images to enhance the blog post content.
            Focus on finding professional, relevant imagery from Unsplash and Pexels.
            
            Requirements:
            - 1 featured image for header/social sharing
            - 1-2 supporting images for main sections
            - High-resolution, professional quality
            - Proper licensing verification
            - SEO-optimized alt text and attributions""",
            
            expected_output="""A curated collection of stock images with metadata:
            - High-quality featured image
            - 1-2 supporting images
            - Complete metadata including URLs, alt text, attributions
            - Photographer credits and licensing information
            - Recommended placement within content""",
            
            agent=self.image_curator(),
            context=[self.write_blog_post_task()],
            output_file="output/images/image_collection_{topic}.json"
        )
    
    @task  
    def publish_content_task(self) -> Task:
        """Create content publishing task for free platforms"""
        return Task(
            description="""Save the completed blog post locally and publish to dev.to platforms.
            
            Workflow:
            1. Save blog post locally in organized directory structure
            2. Create publication instructions for manual publishing
            3. Generate image download scripts
            4. publish to Dev.to if API key is available
            5. Optionally publish to Hashnode if token is available
            6. Provide comprehensive next steps for manual publishing
            
            Platforms to consider:
            - **Dev.to**: Large developer community, completely free
            - **Hashnode**: Developer-focused blogging platform
            - **GitHub Pages**: Free static site hosting
            - **Manual options**: Medium, LinkedIn, personal blog""",
            
            expected_output="""Complete local saving and publication report including:
            - Local directory path with organized files
            - Blog post saved as Markdown with metadata
            - Image collection with download scripts
            - Publication instructions for multiple platforms
            - dev.to API publishing results (if keys available)
            - Manual publishing guidelines
            - Next steps and recommendations
            - Performance tracking suggestions""",
            
            agent=self.content_publisher(),
            context=[self.write_blog_post_task(), self.curate_images_task()],
            output_file="output/published/publication_report_{topic}.json"
        )
    
    @crew
    def crew(self) -> Crew:
        """Create the YouTube Blog automation crew for free publishing"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks, 
            process=Process.sequential,
            verbose=True,
            memory=True,
            embedder={
                "provider": "google",
                "config": {
                    "model": "models/embedding-001",
                    "api_key": os.getenv("GEMINI_API_KEY")
                }
            },
            max_rpm=50,
            language="en"
        )