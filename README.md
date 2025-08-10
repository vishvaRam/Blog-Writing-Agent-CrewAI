# YouTube Blog Automation System

An intelligent agentic AI system using **CrewAI**, **Google Gemini LLM**, and **stock images** to automatically transform YouTube videos into high-quality blog posts and publish them to Medium.

## 🚀 Features

- **Automated YouTube Research**: Finds and analyzes top 3 latest videos on any topic
- **Intelligent Content Creation**: Uses Google Gemini to create 6-10 minute engaging blog posts  
- **Professional Images**: Curates high-quality stock images from Unsplash and Pexels
- **Auto Publishing**: Publishes directly to Medium with proper formatting and SEO
- **Cost Effective**: 87-95% cheaper than OpenAI + DALL-E solutions
- **Multi-Agent System**: 4 specialized AI agents working collaboratively

## 💰 Cost Analysis

| Component | Original Cost | New Cost | Savings |
|-----------|---------------|----------|---------|
| **LLM (OpenAI GPT-4)** | $20-60/month | **FREE** (Gemini Flash) | 100% |
| **Images (DALL-E)** | $40-80/month | **FREE** (Stock APIs) | 100% |
| **Premium LLM** | - | $7.50/month (Gemini Pro) | - |
| **Total** | $60-140/month | $0-7.50/month | **87-95%** |

## 🏗️ Project Structure

```
youtube-blog-automation/
├── 📄 main.py                      # Main execution script
├── 📄 requirements.txt             # Python dependencies
├── 📄 .env.example                 # Environment variables template
├── 📄 .gitignore                   # Git ignore file
├── 📄 README.md                    # This file
├── 📁 config/
│   ├── 📄 agents.yaml              # Agent configurations
│   └── 📄 tasks.yaml               # Task configurations
├── 📁 tools/
│   ├── 📄 __init__.py
│   ├── 📄 youtube_tools.py         # YouTube API tools
│   ├── 📄 content_tools.py         # Content writing tools
│   ├── 📄 stock_image_tools.py     # Stock image API tools
│   └── 📄 publishing_tools.py      # Medium publishing tools
├── 📁 crew/
│   ├── 📄 __init__.py
│   └── 📄 youtube_blog_crew.py     # Main crew definition
├── 📁 output/
│   ├── 📁 research/                # Video research outputs
│   ├── 📁 content/                 # Generated blog posts
│   ├── 📁 images/                  # Downloaded images
│   └── 📁 published/               # Publication reports
└── 📁 utils/
    ├── 📄 __init__.py
    ├── 📄 config_manager.py        # Configuration utilities
    └── 📄 logger.py                # Logging setup
```

## 🛠️ Installation

### Prerequisites

- Python 3.8 or higher
- Git

### Quick Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd youtube-blog-automation
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env file with your API keys
   ```

## 🔑 API Keys Setup

### Required API Keys (All FREE!)

1. **Google Gemini API** (FREE)
   - Visit: https://ai.google.dev/
   - Get API key for free
   - Add to `.env`: `GEMINI_API_KEY=your_key_here`

2. **YouTube Data API v3** (FREE)
   - Visit: https://console.cloud.google.com/
   - Enable YouTube Data API v3
   - Add to `.env`: `YOUTUBE_API_KEY=your_key_here`

3. **Medium Integration Token** (FREE)
   - Medium > Settings > Security and apps > Integration tokens
   - Add to `.env`: `MEDIUM_INTEGRATION_TOKEN=your_token_here`

4. **Unsplash API** (FREE - Unlimited requests)
   - Visit: https://unsplash.com/developers
   - Add to `.env`: `UNSPLASH_ACCESS_KEY=your_key_here`

5. **Pexels API** (FREE - 200 requests/hour)
   - Visit: https://www.pexels.com/api/
   - Add to `.env`: `PEXELS_API_KEY=your_key_here`

## 🚀 Usage

### Basic Usage

```bash
python main.py
```

Then enter your topic when prompted:
```
Enter the topic for blog creation: artificial intelligence trends 2025
```

### Advanced Usage

You can customize the behavior by modifying the configuration in your `.env` file:

```env
# Content Settings
TARGET_READ_TIME=8
MIN_WORD_COUNT=1500
MAX_WORD_COUNT=2500
MAX_VIDEOS_PER_TOPIC=3

# Publishing Settings
DEFAULT_PLATFORM=medium
PUBLISH_STATUS=draft  # or 'public' for immediate publishing
```

## 🤖 AI Agents

### 1. YouTube Researcher Agent
- **LLM**: Gemini 2.0 Flash
- **Role**: Finds top 3 latest videos on any topic
- **Tools**: YouTube Data API, YouTube Transcript API
- **Output**: Comprehensive research with transcripts

### 2. Content Writer Agent  
- **LLM**: Gemini 2.5 Flash (Premium)
- **Role**: Creates 6-10 minute engaging blog posts
- **Tools**: Content structuring, SEO optimization
- **Output**: Publication-ready blog content

### 3. Image Curator Agent
- **LLM**: Gemini 2.0 Flash  
- **Role**: Selects professional stock images
- **Tools**: Unsplash API, Pexels API, Image optimizer
- **Output**: Curated image collection with metadata

### 4. Content Publisher Agent
- **LLM**: Gemini 2.0 Flash
- **Role**: Publishes to Medium with proper formatting
- **Tools**: Medium API, Content formatter, Publication tracker
- **Output**: Published blog post with analytics

## 📊 Workflow Process

1. **Research Phase** (2-3 minutes)
   - Search YouTube for latest videos on topic
   - Extract and analyze transcripts
   - Quality assessment and content curation

2. **Writing Phase** (3-4 minutes)  
   - Synthesize insights from multiple videos
   - Create structured, SEO-optimized content
   - Generate compelling headlines and meta descriptions

3. **Image Curation** (1-2 minutes)
   - Search stock photo APIs for relevant images
   - Optimize images for web and SEO
   - Generate alt text and attributions

4. **Publishing Phase** (1-2 minutes)
   - Format content for Medium platform
   - Configure tags, metadata, and settings
   - Publish and track performance

**Total Time**: 7-11 minutes per blog post

## 🎯 Output Examples

### Research Report
```
output/research/video_research_ai_trends.md
├── Executive summary
├── Video 1: Analysis and transcript  
├── Video 2: Analysis and transcript
├── Video 3: Analysis and transcript
└── Key insights and recommendations
```

### Blog Post
```
output/content/blog_post_ai_trends.md
├── SEO-optimized title and meta description
├── Engaging introduction with hook
├── 4-6 main sections with subheadings  
├── 1,500-2,500 words of valuable content
├── Strong conclusion with takeaways
└── Proper source attribution
```

### Image Collection
```
output/images/image_collection_ai_trends.json
├── Featured image (1200x630px)
├── 3-4 supporting images (800x450px)
├── SEO-optimized alt text
├── Photographer attributions
└── Usage recommendations
```

### Publication Report
```
output/published/publication_report_ai_trends.json
├── Medium post URL and metrics
├── Publication timestamp
├── SEO configuration
├── Performance tracking setup
└── Success/error status
```

## 🔧 Configuration

### Content Configuration
```python
# Modify in .env file or utils/config_manager.py
TARGET_READ_TIME=8          # Minutes
MIN_WORD_COUNT=1500         # Words
MAX_WORD_COUNT=2500         # Words  
MAX_VIDEOS_PER_TOPIC=3      # Videos to analyze
IMAGE_COUNT=4               # Images per post
```

### Publishing Configuration
```python
DEFAULT_PLATFORM=medium     # Publishing platform
PUBLISH_STATUS=draft        # draft, public, unlisted
AUTO_PUBLISH=false          # Auto-publish immediately
SCHEDULE_DELAY_HOURS=0      # Delay before publishing
```

## 📝 Logging

The system provides comprehensive logging:

- **Console Output**: Real-time progress and status
- **Daily Logs**: `logs/youtube_blog_automation_YYYYMMDD.log`
- **Error Logs**: `logs/errors_YYYYMMDD.log`
- **API Tracking**: All API calls logged for monitoring

## 🔍 Troubleshooting

### Common Issues

1. **Missing API Keys**
   ```bash
   Error: Missing required environment variables
   Solution: Check your .env file and ensure all API keys are set
   ```

2. **YouTube Transcript Not Available**
   ```bash
   Error: No transcript available for this video
   Solution: The system will automatically skip and find alternative videos
   ```

3. **Medium Publishing Failed**  
   ```bash
   Error: Failed to create post: 401 - Unauthorized
   Solution: Verify your Medium integration token is correct
   ```

4. **Rate Limit Exceeded**
   ```bash
   Error: API rate limit exceeded
   Solution: Wait and retry, or upgrade API plan if needed
   ```

### Debug Mode

Enable detailed logging for troubleshooting:
```bash
export LOG_LEVEL=DEBUG
python main.py
```

## 🚦 Rate Limits

| API | Free Tier Limit | Recommended Usage |
|-----|-----------------|-------------------|
| **Gemini Flash** | 1M tokens/month | ✅ Sufficient for 100+ blogs |
| **YouTube Data** | 10K units/day | ✅ ~100 searches per day |
| **Medium API** | 15 posts/day | ✅ More than adequate |
| **Unsplash** | Unlimited | ✅ No restrictions |
| **Pexels** | 200/hour | ✅ 50 blog posts per hour |

## 🔐 Security

- Never commit API keys to version control
- Use `.env` files for local development
- Consider using environment variables in production
- Regularly rotate API keys for security

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **CrewAI** for the amazing multi-agent framework
- **Google** for providing free Gemini API access
- **Unsplash & Pexels** for free high-quality stock images  
- **Medium** for their developer-friendly publishing API
- **YouTube** for comprehensive transcript API

## 📞 Support

For support and questions:
- Create an issue in this repository
- Check the troubleshooting section above
- Review the logs for detailed error information

---

**Built with ❤️ using CrewAI and Google Gemini**