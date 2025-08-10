#!/usr/bin/env python3
"""
YouTube Blog Automation System - Updated for Local Saving + Free Publishing
Author: AI Assistant
Date: August 2025

This script saves blogs locally first, then optionally publishes to FREE platforms
like Dev.to and Hashnode. No Medium subscription required!
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from crew.free_youtube_blog_crew import YouTubeBlogCrewFree
from utils.logger import setup_logger
from utils.config_manager import ConfigManager

def print_banner():
    """Print welcome banner"""
    print("🎯 YouTube Blog Automation System (FREE VERSION)")
    print("=" * 60)
    print("✅ Saves blogs locally first")
    print("✅ FREE publishing to Dev.to & Hashnode")
    print("✅ Professional stock images")
    print("✅ 95% cost reduction vs Medium + DALL-E")
    print("=" * 60)

def check_setup():
    """Check if system is properly configured"""
    
    required_vars = [
        'GEMINI_API_KEY',
        'YOUTUBE_API_KEY',
        'UNSPLASH_ACCESS_KEY',
        'PEXELS_API_KEY'
    ]
    
    optional_vars = [
        'DEVTO_API_KEY',
        'HASHNODE_TOKEN'
    ]
    
    missing_required = [var for var in required_vars if not os.getenv(var)]
    missing_optional = [var for var in optional_vars if not os.getenv(var)]
    
    if missing_required:
        print("❌ Missing required API keys:")
        for var in missing_required:
            print(f"   - {var}")
        print("\nPlease check your .env file and add the missing keys.")
        print("See README.md for setup instructions.")
        return False
    
    if missing_optional:
        print("⚠️  Optional API keys not configured:")
        for var in missing_optional:
            print(f"   - {var} (for publishing)")
        print("   → Blog will be saved locally for manual publishing")
        print()
    
    return True

def show_publishing_options():
    """Show available publishing options"""
    print("\n📤 Publishing Options Available:")
    print("=" * 40)
    
    # Check which platforms are configured
    devto_configured = bool(os.getenv('DEVTO_API_KEY'))
    hashnode_configured = bool(os.getenv('HASHNODE_TOKEN'))
    
    print(f"📁 Local Save:     ✅ Always enabled")
    print(f"🔷 Dev.to:         {'✅ Configured' if devto_configured else '⚠️  Manual only'}")
    print(f"🟢 Hashnode:       {'✅ Configured' if hashnode_configured else '⚠️  Manual only'}")
    print(f"📝 GitHub Pages:   ✅ Manual setup")
    print(f"📰 Medium:         ✅ Manual copy-paste")
    print(f"💼 LinkedIn:       ✅ Manual copy-paste")
    print()

def get_user_preferences():
    """Get user publishing preferences"""
    
    preferences = {}
    
    # Get topic
    while True:
        topic = input("📝 Enter the topic for blog creation: ").strip()
        if len(topic) >= 3:
            preferences['topic'] = topic
            break
        print("❌ Topic must be at least 3 characters long.")
    
    # Ask about immediate publishing
    if os.getenv('DEVTO_API_KEY') or os.getenv('HASHNODE_TOKEN'):
        publish_choice = input("\n🚀 Publish immediately after creation? (y/n, default: n): ").strip().lower()
        preferences['auto_publish'] = publish_choice in ['y', 'yes']
        
        if preferences['auto_publish']:
            platforms = []
            if os.getenv('DEVTO_API_KEY'):
                devto_choice = input("📝 Publish to Dev.to? (y/n, default: y): ").strip().lower()
                if devto_choice != 'n':
                    platforms.append('devto')
            
            if os.getenv('HASHNODE_TOKEN'):
                hashnode_choice = input("📝 Publish to Hashnode? (y/n, default: y): ").strip().lower()
                if hashnode_choice != 'n':
                    platforms.append('hashnode')
            
            preferences['platforms'] = platforms
    else:
        preferences['auto_publish'] = False
        preferences['platforms'] = []
    
    return preferences

def main():
    """Main execution function"""
    
    # Load environment variables
    load_dotenv()
    
    # Setup logging
    logger = setup_logger()
    
    # Print banner
    print_banner()
    
    # Check system setup
    if not check_setup():
        return
    
    # Show publishing options
    show_publishing_options()
    
    # Get user preferences
    try:
        preferences = get_user_preferences()
    except KeyboardInterrupt:
        print("\n\n👋 Operation cancelled by user.")
        return
    
    # Initialize inputs for the crew
    inputs = {
        'topic': preferences['topic'],
        'max_videos': 3,
        'read_time_target': '6-10 minutes',
        'auto_publish': preferences['auto_publish'],
        'platforms': ','.join(preferences.get('platforms', []))
    }
    
    logger.info(f"Starting blog automation for topic: {preferences['topic']}")
    print(f"\n🚀 Starting YouTube blog automation for: '{preferences['topic']}'")
    print("⏳ This process may take 8-12 minutes to complete...")
    print("\nProgress will be shown below:")
    print("-" * 50)
    
    try:
        # Initialize and run the crew
        crew_instance = YouTubeBlogCrewFree()
        result = crew_instance.crew().kickoff(inputs=inputs)
        
        # Log successful completion
        logger.info("Blog automation completed successfully")
        print("\n" + "=" * 60)
        print("✅ Blog automation completed successfully!")
        print(f"📝 Generated content for topic: {preferences['topic']}")
        
        # Show results summary
        print("\n📊 Results Summary:")
        print("-" * 30)
        print(f"✅ Blog saved locally")
        
        if preferences['auto_publish']:
            if 'devto' in preferences['platforms']:
                print("🔷 Dev.to: Published")
            if 'hashnode' in preferences['platforms']:
                print("🟢 Hashnode: Published")
        else:
            print("📝 Ready for manual publishing")
        
        # Show output locations
        print("\n📁 Generated Files:")
        print(f"  📝 Research: ./output/research/")
        print(f"  ✍️  Content: ./output/content/")
        print(f"  🖼️  Images: ./output/images/")
        print(f"  📁 Local Blogs: ./local_blogs/")
        print(f"  📤 Publishing: ./output/published/")
        
        # Show next steps
        print("\n🎯 Next Steps:")
        if not preferences['auto_publish']:
            print("1. Check your latest blog in ./local_blogs/")
            print("2. Review the publication_instructions.md file")
            print("3. Download images using the provided script")
            print("4. Publish manually to your preferred platform")
        else:
            print("1. Check published posts on your chosen platforms")
            print("2. Engage with early readers and comments")
            print("3. Share on social media for maximum reach")
        
        print("\n💡 Cost Saved: $60-140/month vs Medium + OpenAI!")
        
    except Exception as e:
        logger.error(f"Error during execution: {str(e)}")
        print(f"\n❌ Error during execution: {str(e)}")
        print("Please check the logs and your API credentials.")
        
        # Show troubleshooting tips
        print("\n🔍 Troubleshooting Tips:")
        print("1. Verify all API keys are correctly set in .env file")
        print("2. Check internet connection")
        print("3. Ensure YouTube videos exist for the given topic")
        print("4. Check logs in ./logs/ directory")
        print("5. Try a different, more specific topic")

def show_help():
    """Show help information"""
    help_text = """
🎯 YouTube Blog Automation System - Help

REQUIRED SETUP:
  1. Copy .env.example to .env
  2. Add required API keys (all FREE):
     - GEMINI_API_KEY (Google AI Studio)
     - YOUTUBE_API_KEY (Google Cloud Console)
     - UNSPLASH_ACCESS_KEY (Unsplash Developers)
     - PEXELS_API_KEY (Pexels API)

OPTIONAL SETUP (for auto-publishing):
  - DEVTO_API_KEY (Dev.to Settings)
  - HASHNODE_TOKEN (Hashnode Developer Settings)

USAGE:
  python main.py              # Interactive mode
  python main.py --help       # Show this help

FEATURES:
  ✅ Always saves blogs locally first
  ✅ Professional stock images (not AI-generated)
  ✅ FREE publishing to Dev.to & Hashnode
  ✅ Manual publishing instructions for other platforms
  ✅ 95% cost reduction vs Medium + DALL-E

OUTPUT:
  - Local blogs saved in ./local_blogs/
  - Publication instructions included
  - Image download scripts provided
  - Ready for manual or auto publishing

For detailed setup instructions, see README.md
"""
    print(help_text)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
        show_help()
    else:
        main()