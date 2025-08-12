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
from tools.free_publishing_tools import LocalBlogSaverTool, DevToPublisherTool 

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
            temperature=0.8
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
            max_iter=3,
            memory=True
        )
    
    @agent  
    def content_writer(self) -> Agent:
        """Create AI blog content writer agent"""
        return Agent(
            role="AI Blog Content Writer and SEO Specialist",
            goal="Transform video transcripts into engaging, well-structured blog posts optimized for Dev.to publication with 6-10 minute read time that provide genuine value to developers",
            backstory="""You are a skilled content writer with expertise in creating engaging long-form blog content 
            that ranks well on search engines and performs excellently on developer platforms like Dev.to. 
            You understand how to structure information for maximum reader engagement, synthesize insights from 
            multiple sources, and create compelling narratives that resonate with technical audiences.
            
            **Dev.to Optimization**: Focus on developer-friendly content with proper markdown formatting, 
            code examples where relevant, and tags that appeal to the Dev.to community. Ensure content 
            is structured for easy scanning with clear headings, bullet points, and actionable insights.""",
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
            complement written content and enhance the overall user experience. 
            
            **Important**: If you cannot find suitable images that directly relate to the blog post topic, 
            prioritize abstract or technology-themed images instead. These serve as effective visual elements 
            that maintain professional aesthetics while avoiding irrelevant or poor-quality imagery.""",
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
            goal="Save blog posts locally and publish directly to Dev.to website as blog posts with proper formatting and metadata",
            backstory="""You are a publishing automation expert who ensures content is properly saved locally first, 
            then distributed to free publishing platforms. You handle local organization, backup, and automated publishing 
            to developer-friendly platforms like Dev.to and Hashnode.
            
            **Primary Focus**: Your main responsibility is to publish content directly to the Dev.to website 
            as blog posts. Ensure all posts are formatted correctly for Dev.to's markdown system, include 
            appropriate tags, and maintain professional presentation standards.""",
            tools=[
                LocalBlogSaverTool(),
                DevToPublisherTool(),
            ],
            llm=self.gemini_flash,
            verbose=True,
            allow_delegation=False,
            max_iter=3,
            memory=True
        )

    
    @task
    def research_videos_task(self) -> Task:
        """Create video research task"""
        return Task(
            description="""Research and find the top 3 most recent, high-quality YouTube videos related to the topic: {topic}.
            
            Steps:
            1. Use YouTube Data API to search for recent videos on the specified topic
            2. Filter by relevance, duration (prefer 10+ minutes), and engagement metrics
            3. Extract full transcripts from each selected video
            4. Analyze content quality and identify key insights
            5. Compile comprehensive research findings""",
            
            expected_output="""A comprehensive research report in Markdown format containing:
            - Executive summary of findings
            - Detailed information for each of the 3 videos
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
            Target 6-10 minute read time (1,500-2,500 words) with high-quality, valuable content.
            
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
            - 1,500-2,500 word count
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
            
            **Fallback Strategy**: If suitable topic-specific images are not available, prioritize 
            abstract or technology-themed images that maintain professional aesthetics.
            
            Requirements:
            - 1 featured image for header/social sharing
            - 1-2 supporting images for main sections
            - High-resolution, professional quality
            - Proper licensing verification
            - SEO-optimized alt text and attributions
            - If no relevant images found, use abstract/tech imagery as fallback""",
            
            expected_output="""A curated collection of stock images with metadata:
            - High-quality featured image (topic-relevant or abstract/tech fallback)
            - 1-2 supporting images (topic-relevant or abstract/tech fallback)
            - Complete metadata including URLs, alt text, attributions
            - Photographer credits and licensing information
            - Recommended placement within content
            - Clear indication if fallback images were used""",
            
            agent=self.image_curator(),
            context=[self.write_blog_post_task()],
            output_file="output/images/image_collection_{topic}.json"
        )

    
    @task  
    def publish_content_task(self) -> Task:
        """Create content publishing task for free platforms"""
        return Task(
            description="""Save the completed blog post locally and publish directly to Dev.to website as a blog post.
            
            **Primary Workflow**:
            1. Save blog post locally in organized directory structure
            2. **Publish directly to Dev.to website** using proper markdown formatting
            3. Generate image download scripts for Dev.to integration
            4. Ensure proper tagging and metadata for Dev.to
            5. Verify publication success and provide confirmation
            6. Create backup publication instructions for manual fallback
            
            **Dev.to Focus**: Prioritize direct publication to Dev.to platform with:
            - Proper markdown formatting for Dev.to standards
            - Appropriate tags for developer audience
            - Featured image optimization for Dev.to
            - Professional presentation and SEO optimization
            **IMPORTANT**: When calling the Dev.to Publisher tool, structure the input as:
            {
                "title": "Blog Title",
                "content": "Full markdown content",
                "tags": "ai,programming,tech",
                "published": true
            }
            Secondary platforms to consider if needed:
            - **Hashnode**: Developer-focused blogging platform
            - **Manual options**: Medium, LinkedIn, personal blog""",
            
            expected_output="""Complete publication report with Dev.to focus:
            - Local directory path with organized files
            - Blog post saved as Markdown with Dev.to-compatible metadata
            - **Dev.to publication confirmation** with post URL and metrics
            - Image collection optimized for Dev.to platform
            - Dev.to-specific formatting verification
            - Publication success status and analytics setup
            - Backup manual publishing guidelines (if needed)
            - Next steps for Dev.to community engagement
            - Performance tracking for Dev.to metrics""",
            
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