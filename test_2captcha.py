#!/usr/bin/env python3


import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper_gui import WebScraperGUI
import tkinter as tk

def test_2captcha_integration():
    """Test the 2Captcha integration"""
    print("🔐 Testing 2Captcha Integration (Python 3.13)")
    print("=" * 60)

    # Create a simple test window
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    # Create scraper instance
    scraper = WebScraperGUI(root)

    # Test URL (using a simple, non-blocked site first)
    test_url = "https://httpbin.org/user-agent"

    print(f"Testing URL: {test_url}")
    print("Testing static scraping with 2Captcha integration...")

    try:
        # Test static scraping
        results, html_content = scraper.scrape_static(
            url=test_url,
            tag="pre"  # httpbin.org returns user agent in <pre> tag
        )

        print("✅ Static scraping successful!")
        print(f"Results: {results}")

        # Check if we got the user agent back
        if 'tag' in results and results['tag']:
            print(f"✅ User agent detected: {results['tag'][0][:100]}...")
        else:
            print("⚠️ No user agent found in results")

    except Exception as e:
        print(f"❌ Static scraping failed: {e}")

    print("\n" + "=" * 60)
    print("2Captcha Integration Test completed!")
    print("\nTo test with a real captcha:")
    print("1. Run: py scraper_gui.py")
    print("2. Enable 'Auto-solve Captchas' checkbox")
    print("3. Enter your 2Captcha API key")
    print("4. Try scraping a protected site like Alibaba.com")

    # Clean up
    root.destroy()

if __name__ == "__main__":
    test_2captcha_integration()
