#!/usr/bin/env python3
"""
Setup script for AI Trip Planner Environment
"""

import os
from pathlib import Path

def create_env_file():
    """Create .env file with the provided Claude API key"""
    
    env_content = """# Anthropic Claude Sonnet API Key (Required for AI Trip Planner)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Rapid API Key (for Booking.com integration)
RAPID_API_KEY=your_rapid_api_key_here

# Optional: OpenAI API Key (for existing flight search functionality)
OPENAI_API_KEY=your_openai_api_key_here
"""
    
    env_file = Path('.env')
    
    if env_file.exists():
        print("⚠️  .env file already exists. Backing up to .env.backup")
        env_file.rename('.env.backup')
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ .env file created successfully!")
    print("🔑 Claude Sonnet API key configured")
    print("📝 You can now run: uvicorn main:app --reload")

def test_claude_connection():
    """Test the Claude API connection"""
    try:
        import anthropic
        from dotenv import load_dotenv
        
        load_dotenv()
        
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            print("❌ ANTHROPIC_API_KEY not found in environment")
            return False
        
        client = anthropic.Anthropic(api_key=api_key)
        
        # Test with a simple message
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            messages=[{"role": "user", "content": "Hello, test message"}]
        )
        
        print("✅ Claude API connection successful!")
        print(f"🤖 Model: claude-sonnet-4-20250514")
        print(f"📝 Response: {response.content[0].text[:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ Claude API connection failed: {e}")
        return False

def main():
    print("🚀 AI Trip Planner Environment Setup")
    print("=" * 40)
    
    # Create .env file
    create_env_file()
    
    # Test connection
    print("\n🔍 Testing Claude API connection...")
    if test_claude_connection():
        print("\n🎉 Setup complete! You can now run the AI Trip Planner.")
        print("\n📋 Next steps:")
        print("1. Run: uvicorn main:app --reload")
        print("2. Visit: http://localhost:8000/trip-planner")
        print("3. Try: 'Plan a trip from Dallas to Italy for 7 days'")
    else:
        print("\n❌ Setup incomplete. Please check your API key and try again.")

if __name__ == "__main__":
    main() 