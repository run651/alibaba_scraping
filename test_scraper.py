#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced web scraper capabilities
Compatible with Python 3.13
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper_gui import WebScraperGUI
import tkinter as tk

def test_scraper():
    """Test the enhanced scraper with a simple example"""
    print("🚀 Testing Enhanced Web Scraper (Python 3.13)")
    print("=" * 50)
    
    # Create a simple test window
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    # Create scraper instance
    scraper = WebScraperGUI(root)
    
    # Test URL (using a simple, non-blocked site)
    test_url = "https://httpbin.org/user-agent"
    
    print(f"Testing URL: {test_url}")
    print("Testing static scraping with enhanced headers...")
    
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
    
    print("\n" + "=" * 50)
    print("Test completed!")
    
    # Clean up
    root.destroy()

if __name__ == "__main__":
    test_scraper()
