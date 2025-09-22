import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import requests
from bs4 import BeautifulSoup
from lxml import html
import threading
import json
import csv
from datetime import datetime
import os
import sys
from urllib.parse import urljoin, urlparse
from PIL import Image, ImageTk
import io
import base64
import math

# Configure Playwright browsers path to bundled folder when frozen
def _resource_path(relative_path: str) -> str:
    base_path = getattr(sys, '_MEIPASS', os.path.abspath('.'))
    return os.path.join(base_path, relative_path)

_bundled_browsers = _resource_path('playwright-browsers')
if os.path.isdir(_bundled_browsers):
    os.environ['PLAYWRIGHT_BROWSERS_PATH'] = _bundled_browsers

# Configure certs for Requests/OpenSSL when frozen
try:
    import certifi
    ca_bundle_path = certifi.where()
    if os.path.isfile(ca_bundle_path):
        os.environ['SSL_CERT_FILE'] = ca_bundle_path
        os.environ['REQUESTS_CA_BUNDLE'] = ca_bundle_path
except Exception:
    pass

from playwright.sync_api import sync_playwright


class WebScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Webスクレイパー - GUI 版")
        self.root.geometry("800x700")
        self.root.configure(bg='#f0f0f0')
        
        # Variables
        self.url_var = tk.StringVar(value="https://example.com")
        self.scraping_type = tk.StringVar(value="static")
        self.tag_var = tk.StringVar()
        self.class_var = tk.StringVar()
        self.id_var = tk.StringVar()
        self.css_var = tk.StringVar()
        self.xpath_var = tk.StringVar()
        
        # Proxy settings
        self.use_proxy = tk.BooleanVar(value=False)
        self.proxy_url = tk.StringVar(value="http://proxy:port")
        
        # 2Captcha settings
        self.use_2captcha = tk.BooleanVar(value=False)
        self.captcha_api_key = tk.StringVar(value="2dc9c11d4193f0d3501b18cd8c568f60")
        
        # Image extraction disabled
        # self.extract_images = tk.BooleanVar(value=False)
        # self.image_folder = tk.StringVar(value="downloaded_images")
        # self.max_images = tk.StringVar(value="50")
        # self.image_min_size = tk.StringVar(value="100")
        
        # Pause functionality
        self.is_paused = False
        self.pause_event = threading.Event()
        self.scraping_thread = None
        
        # Stop functionality
        self.should_stop = False
        self.stop_event = threading.Event()
        
        # Check Playwright installation
        self.check_playwright_setup()
        
        self.setup_ui()
    
    def check_playwright_setup(self):
        """Check if Playwright browsers are installed"""
        try:
            from playwright.sync_api import sync_playwright
            p = sync_playwright().start()
            # Try to launch browser to check if it's installed
            browser = p.chromium.launch(headless=True)
            browser.close()
            p.stop()
        except Exception as e:
            # Show warning about Playwright setup
            import tkinter.messagebox as mb
            mb.showwarning(
                "Playwright のセットアップが必要です", 
                f"Playwright のブラウザがインストールされていません。\n\n"
                f"インストールするまで Dynamic モードは使用できません。\n\n"
                f"インストールするには次を実行してください:\n"
                f"py -m playwright install chromium\n\n"
                f"エラー: {str(e)}"
            )
    
    def detect_captcha_or_blocking(self, html_content):
        """Detect if the page contains captcha or blocking mechanisms"""
        captcha_indicators = [
            "captcha", "unusual traffic", "verify you are human", "robot", "bot detection",
            "access denied", "blocked", "suspicious activity", "security check",
            "please wait", "verification required", "challenge", "nocaptcha", "recaptcha",
            "hcaptcha", "cloudflare", "ddos protection", "rate limit", "too many requests",
            "captcha-loading", "nc_token", "x5secdata", "nc-verify-form", "bx-feedback-btn",
            "alibaba.com", "punish", "verification", "security", "challenge", "slide to verify",
            "nc_1_nocaptcha", "nc-container", "slidetounlock"
        ]
        
        html_lower = html_content.lower()
        for indicator in captcha_indicators:
            if indicator in html_lower:
                return True
        return False
    
    def detect_captcha_type(self, html_content):
        """Detect the specific type of captcha present"""
        html_lower = html_content.lower()
        
        # Check for Alibaba NoCaptcha slider
        if "nc_1_nocaptcha" in html_content or "slidetounlock" in html_lower or "slide to verify" in html_lower:
            return "alibaba_nocaptcha"
        
        # Check for reCAPTCHA v2
        if "g-recaptcha" in html_content or "recaptcha" in html_lower:
            return "recaptcha_v2"
        
        # Check for hCaptcha
        if "hcaptcha" in html_lower:
            return "hcaptcha"
        
        # Check for image captcha
        if "captcha" in html_lower and ("img" in html_lower or "image" in html_lower):
            return "image_captcha"
        
        # Check for Cloudflare
        if "cloudflare" in html_lower or "cf-challenge" in html_lower:
            return "cloudflare"
        
        return "unknown"
    
    def get_random_user_agent(self):
        """Get a random realistic user agent"""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
        ]
        import random
        return random.choice(user_agents)
    
    def is_ecommerce_site(self, url):
        """Check if the URL is from a known e-commerce site with strict anti-bot protection"""
        ecommerce_domains = [
            "alibaba.com", "aliexpress.com", "amazon.com", "ebay.com", "walmart.com",
            "target.com", "bestbuy.com", "homedepot.com", "lowes.com", "costco.com",
            "wayfair.com", "overstock.com", "zappos.com", "nordstrom.com", "macys.com"
        ]
        
        url_lower = url.lower()
        for domain in ecommerce_domains:
            if domain in url_lower:
                return True
        return False
    
    def get_enhanced_stealth_script(self):
        """Get enhanced stealth script for better anti-detection"""
        return """
        // Enhanced stealth script for better anti-detection
        
        // Remove webdriver property completely
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        // Mock plugins array with realistic data
        Object.defineProperty(navigator, 'plugins', {
            get: () => {
                return {
                    0: {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer'},
                    1: {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'},
                    2: {name: 'Native Client', filename: 'internal-nacl-plugin'},
                    length: 3
                };
            },
        });
        
        // Mock languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
        
        // Mock permissions API
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // Mock chrome runtime
        window.chrome = {
            runtime: {
                onConnect: undefined,
                onMessage: undefined,
            },
        };
        
        // Remove automation indicators
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_JSON;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Object;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Proxy;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Reflect;
        
        // Mock screen properties
        Object.defineProperty(screen, 'availHeight', {get: () => 1040});
        Object.defineProperty(screen, 'availWidth', {get: () => 1920});
        Object.defineProperty(screen, 'colorDepth', {get: () => 24});
        Object.defineProperty(screen, 'height', {get: () => 1080});
        Object.defineProperty(screen, 'pixelDepth', {get: () => 24});
        Object.defineProperty(screen, 'width', {get: () => 1920});
        
        // Mock timezone
        Object.defineProperty(Intl, 'DateTimeFormat', {
            value: function() {
                return {
                    resolvedOptions: () => ({timeZone: 'America/New_York'})
                };
            }
        });
        
        // Mock hardware concurrency
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 8,
        });
        
        // Mock device memory
        Object.defineProperty(navigator, 'deviceMemory', {
            get: () => 8,
        });
        
        // Mock connection
        Object.defineProperty(navigator, 'connection', {
            get: () => ({
                effectiveType: '4g',
                rtt: 50,
                downlink: 10
            }),
        });
        """
    
    def solve_2captcha(self, captcha_type, page_url, site_key=None, captcha_image=None):
        """Solve captcha using 2Captcha service"""
        if not self.use_2captcha.get() or not self.captcha_api_key.get().strip():
            return None
            
        api_key = self.captcha_api_key.get().strip()
        
        try:
            if captcha_type == "recaptcha_v2":
                return self._solve_recaptcha_v2(api_key, page_url, site_key)
            elif captcha_type == "image":
                return self._solve_image_captcha(api_key, captcha_image)
            elif captcha_type == "hcaptcha":
                return self._solve_hcaptcha(api_key, page_url, site_key)
            else:
                self.root.after(0, lambda: self.append_result(f"  ⚠️ Unsupported captcha type: {captcha_type}\n"))
                return None
        except Exception as e:
            self.root.after(0, lambda: self.append_result(f"  ❌ 2Captcha error: {str(e)}\n"))
            return None
    
    def _solve_recaptcha_v2(self, api_key, page_url, site_key):
        """Solve reCAPTCHA v2 using 2Captcha"""
        self.root.after(0, lambda: self.append_result("  🔐 Solving reCAPTCHA v2 with 2Captcha...\n"))
        
        # Submit captcha
        submit_data = {
            'key': api_key,
            'method': 'userrecaptcha',
            'googlekey': site_key,
            'pageurl': page_url,
            'json': 1
        }
        
        response = requests.post('http://2captcha.com/in.php', data=submit_data)
        result = response.json()
        
        if result['status'] != 1:
            raise Exception(f"Failed to submit captcha: {result.get('error_text', 'Unknown error')}")
        
        captcha_id = result['request']
        self.root.after(0, lambda: self.append_result(f"  📝 Captcha submitted, ID: {captcha_id}\n"))
        
        # Wait for solution
        for attempt in range(30):  # Wait up to 5 minutes
            time.sleep(10)
            
            check_data = {
                'key': api_key,
                'action': 'get',
                'id': captcha_id,
                'json': 1
            }
            
            response = requests.get('http://2captcha.com/res.php', params=check_data)
            result = response.json()
            
            if result['status'] == 1:
                self.root.after(0, lambda: self.append_result("  ✅ reCAPTCHA solved successfully!\n"))
                return result['request']
            elif result['error_text'] == 'CAPCHA_NOT_READY':
                self.root.after(0, lambda: self.append_result(f"  ⏳ Waiting for solution... ({attempt + 1}/30)\n"))
                continue
            else:
                raise Exception(f"Failed to solve captcha: {result.get('error_text', 'Unknown error')}")
        
        raise Exception("Captcha solving timeout")
    
    def _solve_image_captcha(self, api_key, captcha_image):
        """Solve image captcha using 2Captcha"""
        self.root.after(0, lambda: self.append_result("  🔐 Solving image captcha with 2Captcha...\n"))
        
        # Convert image to base64
        if isinstance(captcha_image, bytes):
            image_b64 = base64.b64encode(captcha_image).decode('utf-8')
        else:
            image_b64 = captcha_image
        
        # Submit captcha
        submit_data = {
            'key': api_key,
            'method': 'base64',
            'body': image_b64,
            'json': 1
        }
        
        response = requests.post('http://2captcha.com/in.php', data=submit_data)
        result = response.json()
        
        if result['status'] != 1:
            raise Exception(f"Failed to submit captcha: {result.get('error_text', 'Unknown error')}")
        
        captcha_id = result['request']
        self.root.after(0, lambda: self.append_result(f"  📝 Image captcha submitted, ID: {captcha_id}\n"))
        
        # Wait for solution
        for attempt in range(30):  # Wait up to 5 minutes
            time.sleep(10)
            
            check_data = {
                'key': api_key,
                'action': 'get',
                'id': captcha_id,
                'json': 1
            }
            
            response = requests.get('http://2captcha.com/res.php', params=check_data)
            result = response.json()
            
            if result['status'] == 1:
                self.root.after(0, lambda: self.append_result("  ✅ Image captcha solved successfully!\n"))
                return result['request']
            elif result['error_text'] == 'CAPCHA_NOT_READY':
                self.root.after(0, lambda: self.append_result(f"  ⏳ Waiting for solution... ({attempt + 1}/30)\n"))
                continue
            else:
                raise Exception(f"Failed to solve captcha: {result.get('error_text', 'Unknown error')}")
        
        raise Exception("Captcha solving timeout")
    
    def _solve_hcaptcha(self, api_key, page_url, site_key):
        """Solve hCaptcha using 2Captcha"""
        self.root.after(0, lambda: self.append_result("  🔐 Solving hCaptcha with 2Captcha...\n"))
        
        # Submit captcha
        submit_data = {
            'key': api_key,
            'method': 'hcaptcha',
            'sitekey': site_key,
            'pageurl': page_url,
            'json': 1
        }
        
        response = requests.post('http://2captcha.com/in.php', data=submit_data)
        result = response.json()
        
        if result['status'] != 1:
            raise Exception(f"Failed to submit captcha: {result.get('error_text', 'Unknown error')}")
        
        captcha_id = result['request']
        self.root.after(0, lambda: self.append_result(f"  📝 hCaptcha submitted, ID: {captcha_id}\n"))
        
        # Wait for solution
        for attempt in range(30):  # Wait up to 5 minutes
            time.sleep(10)
            
            check_data = {
                'key': api_key,
                'action': 'get',
                'id': captcha_id,
                'json': 1
            }
            
            response = requests.get('http://2captcha.com/res.php', params=check_data)
            result = response.json()
            
            if result['status'] == 1:
                self.root.after(0, lambda: self.append_result("  ✅ hCaptcha solved successfully!\n"))
                return result['request']
            elif result['error_text'] == 'CAPCHA_NOT_READY':
                self.root.after(0, lambda: self.append_result(f"  ⏳ Waiting for solution... ({attempt + 1}/30)\n"))
                continue
            else:
                raise Exception(f"Failed to solve captcha: {result.get('error_text', 'Unknown error')}")
        
        raise Exception("Captcha solving timeout")
    
    def solve_alibaba_nocaptcha(self, page, url):
        """Solve Alibaba's NoCaptcha slider using human-like behavior"""
        try:
            self.root.after(0, lambda: self.append_result("  🎯 Detected Alibaba NoCaptcha slider\n"))
            self.root.after(0, lambda: self.append_result("  🤖 Attempting to solve with human-like behavior...\n"))
            
            # Wait for the slider to be visible
            try:
                slider = page.wait_for_selector('#nc_1_n1z', timeout=10000)
                if not slider:
                    self.root.after(0, lambda: self.append_result("  ❌ Slider not found\n"))
                    return False
            except:
                self.root.after(0, lambda: self.append_result("  ❌ Slider not found\n"))
                return False
            
            # Get slider dimensions
            slider_box = slider.bounding_box()
            if not slider_box:
                self.root.after(0, lambda: self.append_result("  ❌ Could not get slider dimensions\n"))
                return False
            
            # Calculate movement distance (slider width - handle width)
            slider_width = slider_box['width']
            handle_width = 40  # Approximate handle width
            move_distance = slider_width - handle_width - 10  # Leave some margin
            
            # Human-like mouse movement to slider
            self.root.after(0, lambda: self.append_result("  🖱️ Moving mouse to slider...\n"))
            
            # Move to slider with human-like behavior
            start_x = slider_box['x'] + 20
            start_y = slider_box['y'] + slider_box['height'] / 2
            
            # Move mouse to slider gradually
            for i in range(5):
                intermediate_x = start_x + (i * 10)
                page.mouse.move(intermediate_x, start_y)
                time.sleep(random.uniform(0.1, 0.3))
            
            # Click and hold on slider
            self.root.after(0, lambda: self.append_result("  🖱️ Clicking and holding slider...\n"))
            page.mouse.move(start_x, start_y)
            time.sleep(random.uniform(0.2, 0.5))
            page.mouse.down()
            time.sleep(random.uniform(0.1, 0.3))
            
            # Human-like drag movement
            self.root.after(0, lambda: self.append_result("  🖱️ Dragging slider...\n"))
            
            # Simulate human-like drag with slight variations
            steps = random.randint(15, 25)
            for i in range(steps):
                progress = i / steps
                
                # Add slight curve to movement (human behavior)
                curve_offset = math.sin(progress * math.pi) * random.uniform(-2, 2)
                
                current_x = start_x + (move_distance * progress) + curve_offset
                current_y = start_y + random.uniform(-1, 1)  # Slight vertical variation
                
                page.mouse.move(current_x, current_y)
                time.sleep(random.uniform(0.05, 0.15))  # Variable timing
            
            # Final position
            final_x = start_x + move_distance
            page.mouse.move(final_x, start_y)
            time.sleep(random.uniform(0.2, 0.5))
            
            # Release mouse
            page.mouse.up()
            time.sleep(random.uniform(0.5, 1.0))
            
            self.root.after(0, lambda: self.append_result("  ✅ Slider drag completed\n"))
            
            # Wait for verification
            self.root.after(0, lambda: self.append_result("  ⏳ Waiting for verification...\n"))
            time.sleep(random.uniform(2, 4))
            
            # Check if verification was successful
            try:
                # Look for success indicators
                success_indicators = [
                    'nc_1_n1t[style*="width: 100%"]',  # Slider filled
                    '.nc_ok',  # Success class
                    '[class*="success"]',  # Success indicator
                ]
                
                for indicator in success_indicators:
                    if page.query_selector(indicator):
                        self.root.after(0, lambda: self.append_result("  ✅ Alibaba NoCaptcha solved successfully!\n"))
                        return True
                
                # Check if page content changed (no more captcha)
                current_content = page.content()
                if not self.detect_captcha_or_blocking(current_content):
                    self.root.after(0, lambda: self.append_result("  ✅ Captcha appears to be solved!\n"))
                    return True
                
                self.root.after(0, lambda: self.append_result("  ⚠️ Verification status unclear, continuing...\n"))
                return True  # Assume success and continue
                
            except Exception as e:
                self.root.after(0, lambda: self.append_result(f"  ⚠️ Verification check failed: {str(e)}\n"))
                return True  # Continue anyway
            
        except Exception as e:
            self.root.after(0, lambda: self.append_result(f"  ❌ Alibaba NoCaptcha solving failed: {str(e)}\n"))
            return False
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        self.setup_controls_ui(main_frame)
    
    def setup_controls_ui(self, main_frame):
        # Title
        title_label = ttk.Label(main_frame, text="Webスクレイパー", font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # URL input
        ttk.Label(main_frame, text="URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        url_entry = ttk.Entry(main_frame, textvariable=self.url_var, width=50)
        url_entry.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Scraping type
        ttk.Label(main_frame, text="スクレイピング種別:").grid(row=2, column=0, sticky=tk.W, pady=5)
        type_frame = ttk.Frame(main_frame)
        type_frame.grid(row=2, column=1, sticky=tk.W, pady=5)
        ttk.Radiobutton(type_frame, text="静的", variable=self.scraping_type, value="static").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(type_frame, text="動的", variable=self.scraping_type, value="dynamic").pack(side=tk.LEFT)
        
        # Proxy settings
        ttk.Label(main_frame, text="プロキシ設定:").grid(row=3, column=0, sticky=tk.W, pady=5)
        proxy_frame = ttk.Frame(main_frame)
        proxy_frame.grid(row=3, column=1, sticky=tk.W, pady=5)
        ttk.Checkbutton(proxy_frame, text="プロキシを使用", variable=self.use_proxy).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Entry(proxy_frame, textvariable=self.proxy_url, width=30).pack(side=tk.LEFT)
        
        # 2Captcha settings
        ttk.Label(main_frame, text="2Captcha 設定:").grid(row=4, column=0, sticky=tk.W, pady=5)
        captcha_frame = ttk.Frame(main_frame)
        captcha_frame.grid(row=4, column=1, sticky=tk.W, pady=5)
        ttk.Checkbutton(captcha_frame, text="Captcha を自動解決", variable=self.use_2captcha).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(captcha_frame, text="APIキー:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(captcha_frame, textvariable=self.captcha_api_key, width=35).pack(side=tk.LEFT)
        
        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Selectors section
        selectors_label = ttk.Label(main_frame, text="コンテンツセレクタ（不要なら空のまま）:", font=('Arial', 10, 'bold'))
        selectors_label.grid(row=6, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        
        # Tag selector
        ttk.Label(main_frame, text="HTML タグ:").grid(row=7, column=0, sticky=tk.W, pady=2)
        ttk.Entry(main_frame, textvariable=self.tag_var, width=20).grid(row=7, column=1, sticky=tk.W, pady=2)
        
        # Class selector
        ttk.Label(main_frame, text="CSS クラス:").grid(row=8, column=0, sticky=tk.W, pady=2)
        ttk.Entry(main_frame, textvariable=self.class_var, width=20).grid(row=8, column=1, sticky=tk.W, pady=2)
        
        # ID selector
        ttk.Label(main_frame, text="要素 ID:").grid(row=9, column=0, sticky=tk.W, pady=2)
        ttk.Entry(main_frame, textvariable=self.id_var, width=20).grid(row=9, column=1, sticky=tk.W, pady=2)
        
        # CSS selector
        ttk.Label(main_frame, text="CSS セレクタ:").grid(row=10, column=0, sticky=tk.W, pady=2)
        ttk.Entry(main_frame, textvariable=self.css_var, width=30).grid(row=10, column=1, sticky=tk.W, pady=2)
        
        # XPath selector
        ttk.Label(main_frame, text="XPath セレクタ:").grid(row=11, column=0, sticky=tk.W, pady=2)
        ttk.Entry(main_frame, textvariable=self.xpath_var, width=30).grid(row=11, column=1, sticky=tk.W, pady=2)
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=12, column=0, columnspan=3, pady=20)
        
        # Scrape button
        self.scrape_btn = ttk.Button(buttons_frame, text="スクレイピング開始", command=self.start_scraping)
        self.scrape_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Pause/Resume button
        self.pause_btn = ttk.Button(buttons_frame, text="一時停止", command=self.toggle_pause, state='disabled')
        self.pause_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Stop button
        self.stop_btn = ttk.Button(buttons_frame, text="停止", command=self.stop_scraping, state='disabled')
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Clear button
        ttk.Button(buttons_frame, text="結果をクリア", command=self.clear_results).pack(side=tk.LEFT, padx=(0, 10))
        
        # Save button
        ttk.Button(buttons_frame, text="結果を保存", command=self.save_results).pack(side=tk.LEFT, padx=(0, 10))
        
        # Install Playwright button
        ttk.Button(buttons_frame, text="Playwright をインストール", command=self.install_playwright).pack(side=tk.LEFT, padx=(0, 10))
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=12, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Results area
        results_label = ttk.Label(main_frame, text="結果:", font=('Arial', 10, 'bold'))
        results_label.grid(row=13, column=0, columnspan=3, sticky=tk.W, pady=(20, 5))
        
        self.results_text = scrolledtext.ScrolledText(main_frame, height=15, width=80)
        self.results_text.grid(row=14, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Configure text widget for images
        self.results_text.configure(state='normal')
        
        # Configure grid weights for resizing
        main_frame.rowconfigure(14, weight=1)
    
    # Image gallery UI disabled
    # def setup_image_gallery_ui(self, frame):
    #     """Setup the image gallery UI"""
    #     # Gallery functionality removed
        
    def start_scraping(self):
        """Start scraping in a separate thread"""
        if not self.url_var.get().strip():
            messagebox.showerror("エラー", "URL を入力してください")
            return
        
        # Check if it's an e-commerce site and warn user
        url = self.url_var.get().strip()
        if self.is_ecommerce_site(url):
            result = messagebox.askyesno(
                "EC サイトを検出", 
                f"厳格なボット対策が施された EC サイトの可能性があります。\n\n"
                f"推奨事項:\n"
                f"• 動的（Dynamic）モードを使用\n"
                f"• プロキシ設定を有効化\n"
                f"• Captcha の発生に備える\n\n"
                f"続行しますか？"
            )
            if not result:
                return
        
        self.scrape_btn.config(state='disabled')
        self.pause_btn.config(state='normal', text="一時停止")
        self.stop_btn.config(state='normal')
        self.is_paused = False
        self.should_stop = False
        self.pause_event.set()  # Ensure pause event is cleared
        self.stop_event.clear()  # Ensure stop event is cleared
        self.progress.start()
        self.results_text.delete(1.0, tk.END)
        
        # Start scraping in a separate thread
        self.scraping_thread = threading.Thread(target=self.scrape_worker)
        self.scraping_thread.daemon = True
        self.scraping_thread.start()
        
    def scrape_worker(self):
        """Worker function for scraping"""
        try:
            # Check for stop before starting
            if self.check_should_stop():
                self.root.after(0, self.scraping_stopped)
                return
                
            url = self.url_var.get().strip()
            scraping_type = self.scraping_type.get()
            
            # Get selector values
            tag = self.tag_var.get().strip() or None
            class_name = self.class_var.get().strip() or None
            id_name = self.id_var.get().strip() or None
            css_selector = self.css_var.get().strip() or None
            xpath_selector = self.xpath_var.get().strip() or None
            
            # Check for stop before scraping
            if self.check_should_stop():
                self.root.after(0, self.scraping_stopped)
                return
            
            # Perform scraping
            if scraping_type == "static":
                results, html_content = self.scrape_static(url, tag, class_name, id_name, css_selector, xpath_selector)
            else:
                results, html_content = self.scrape_dynamic(url, tag, class_name, id_name, css_selector, xpath_selector)

            print(html_content)
            
            # Check for stop before image extraction
            if self.check_should_stop():
                self.root.after(0, self.scraping_stopped)
                return
            
            # Image extraction disabled
            # No image extraction functionality
            
            # Check for stop before completion
            if self.check_should_stop():
                self.root.after(0, self.scraping_stopped)
                return
            
            # Update UI in main thread
            self.root.after(0, self.scraping_complete, results)
            
        except Exception as e:
            if not self.check_should_stop():  # Only show error if not stopped
                self.root.after(0, self.scraping_error, str(e))
            else:
                self.root.after(0, self.scraping_stopped)
    
    def toggle_pause(self):
        """Toggle pause/resume functionality"""
        if self.is_paused:
            # Resume
            self.is_paused = False
            self.pause_event.set()  # Clear the pause event
            self.pause_btn.config(text="一時停止")
            self.append_result("\n[再開] スクレイピングを再開しました...\n")
        else:
            # Pause
            self.is_paused = True
            self.pause_event.clear()  # Set the pause event
            self.pause_btn.config(text="再開")
            self.append_result("\n[一時停止] スクレイピングを一時停止しました。\n『再開』をクリックしてください...\n")
    
    def wait_if_paused(self):
        """Wait if scraping is paused"""
        if self.is_paused:
            self.pause_event.wait()  # This will block until resume is clicked
    
    def check_should_stop(self):
        """Check if scraping should be stopped"""
        return self.should_stop
    
    def stop_scraping(self):
        """Stop the scraping process"""
        self.should_stop = True
        self.stop_event.set()
        self.pause_btn.config(state='disabled', text="一時停止")
        self.stop_btn.config(state='disabled')
        self.append_result("\n[停止] ユーザー操作によりスクレイピングを停止しました...\n")
        
        # Wait a moment for the thread to finish gracefully
        if self.scraping_thread and self.scraping_thread.is_alive():
            self.scraping_thread.join(timeout=2.0)
        
        # Reset UI state
        self.progress.stop()
        self.scrape_btn.config(state='normal')
        self.is_paused = False
    
    def scraping_stopped(self):
        """Called when scraping is stopped"""
        self.progress.stop()
        self.scrape_btn.config(state='normal')
        self.pause_btn.config(state='disabled', text="一時停止")
        self.stop_btn.config(state='disabled')
        self.is_paused = False
        self.append_result("\n" + "="*50 + "\nユーザーによりスクレイピングが停止されました。\n")
    
    def scrape_static(self, url, tag=None, class_name=None, id_name=None, css_selector=None, xpath_selector=None):
        """Static scraping method with enhanced anti-detection"""
        self.root.after(0, lambda: self.append_result(f"[STATIC FETCH] {url}\n"))
        
        # Enhanced headers to mimic real browser
        headers = {
            'User-Agent': self.get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1'
        }
        
        # Add random delay to appear more human-like
        import time
        import random
        delay = random.uniform(1, 3)
        self.root.after(0, lambda: self.append_result(f"  Waiting {delay:.1f}s to appear human-like...\n"))
        time.sleep(delay)
        
        try:
            # Use session for better connection handling
            session = requests.Session()
            session.headers.update(headers)
            
            # Configure proxy if enabled
            proxies = None
            if self.use_proxy.get() and self.proxy_url.get().strip():
                proxy_url = self.proxy_url.get().strip()
                if not proxy_url.startswith(('http://', 'https://')):
                    proxy_url = 'http://' + proxy_url
                proxies = {
                    'http': proxy_url,
                    'https': proxy_url
                }
                self.root.after(0, lambda: self.append_result(f"  Using proxy: {proxy_url}\n"))
            
            # Add retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.root.after(0, lambda: self.append_result(f"  Attempt {attempt + 1}/{max_retries}...\n"))
                    res = session.get(url, timeout=30, allow_redirects=True, proxies=proxies)
                    res.raise_for_status()
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    self.root.after(0, lambda: self.append_result(f"  Retrying in 2s... ({str(e)[:50]}...)\n"))
                    time.sleep(2)
            
            html_content = res.text
            
            # Check if we got a captcha page
            if "captcha" in html_content.lower() or "unusual traffic" in html_content.lower():
                self.root.after(0, lambda: self.append_result("  ⚠️ Captcha detected! Consider using dynamic scraping instead.\n"))
            
            results = self.extract_content(html_content, tag, class_name, id_name, css_selector, xpath_selector)
            return results, html_content
            
        except Exception as e:
            self.root.after(0, lambda: self.append_result(f"  ❌ Static scraping failed: {str(e)}\n"))
            raise e
    
    def scrape_dynamic(self, url, tag=None, class_name=None, id_name=None, css_selector=None, xpath_selector=None):
        """Ultra-robust dynamic scraping method with stealth mode and anti-detection"""
        self.root.after(0, lambda: self.append_result(f"[DYNAMIC FETCH] {url}\n"))
        
        playwright_instance = None
        browser = None
        page = None
        
        try:
            # Initialize Playwright with error handling
            self.root.after(0, lambda: self.append_result("  Initializing Playwright...\n"))
            try:
                playwright_instance = sync_playwright().start()
                self.root.after(0, lambda: self.append_result("  ✅ Playwright initialized successfully.\n"))
            except Exception as e:
                raise Exception(f"Failed to initialize Playwright: {str(e)}")
            
            # Configure proxy if enabled
            proxy_config = None
            if self.use_proxy.get() and self.proxy_url.get().strip():
                proxy_url = self.proxy_url.get().strip()
                if not proxy_url.startswith(('http://', 'https://')):
                    proxy_url = 'http://' + proxy_url
                proxy_config = {"server": proxy_url}
                self.root.after(0, lambda: self.append_result(f"  Using proxy: {proxy_url}\n"))
            
            # Launch browser with stealth mode and anti-detection
            self.root.after(0, lambda: self.append_result("  Launching Chromium browser with stealth mode...\n"))
            try:
                browser = playwright_instance.chromium.launch(
                    headless=True,
                    proxy=proxy_config,
                    args=[
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-extensions',
                        '--no-first-run',
                        '--disable-default-apps',
                        '--disable-background-timer-throttling',
                        '--disable-backgrounding-occluded-windows',
                        '--disable-renderer-backgrounding',
                        '--disable-ipc-flooding-protection',
                        '--disable-hang-monitor',
                        '--disable-prompt-on-repost',
                        '--disable-sync',
                        '--disable-translate',
                        '--disable-logging',
                        '--disable-permissions-api',
                        '--disable-plugins-discovery',
                        '--disable-preconnect',
                        '--disable-print-preview',
                        '--disable-speech-api',
                        '--disable-web-resources',
                        '--hide-scrollbars',
                        '--mute-audio',
                        '--no-default-browser-check',
                        '--no-pings',
                        '--no-zygote',
                        '--disable-background-networking',
                        '--disable-component-extensions-with-background-pages',
                        '--disable-default-apps',
                        '--disable-domain-reliability',
                        '--disable-features=TranslateUI',
                        '--disable-ipc-flooding-protection',
                        '--disable-renderer-backgrounding',
                        '--disable-backgrounding-occluded-windows',
                        '--disable-client-side-phishing-detection',
                        '--disable-sync-preferences',
                        '--disable-background-timer-throttling',
                        '--disable-renderer-backgrounding',
                        '--disable-backgrounding-occluded-windows',
                        '--disable-features=TranslateUI,BlinkGenPropertyTrees',
                        '--disable-ipc-flooding-protection',
                        '--disable-hang-monitor',
                        '--disable-prompt-on-repost',
                        '--disable-sync',
                        '--disable-translate',
                        '--disable-logging',
                        '--disable-permissions-api',
                        '--disable-plugins-discovery',
                        '--disable-preconnect',
                        '--disable-print-preview',
                        '--disable-speech-api',
                        '--disable-web-resources',
                        '--hide-scrollbars',
                        '--mute-audio',
                        '--no-default-browser-check',
                        '--no-pings',
                        '--no-zygote',
                        '--disable-background-networking',
                        '--disable-component-extensions-with-background-pages',
                        '--disable-default-apps',
                        '--disable-domain-reliability',
                        '--disable-features=TranslateUI',
                        '--disable-ipc-flooding-protection',
                        '--disable-renderer-backgrounding',
                        '--disable-backgrounding-occluded-windows',
                        '--disable-client-side-phishing-detection',
                        '--disable-sync-preferences',
                        '--disable-background-timer-throttling',
                        '--disable-renderer-backgrounding',
                        '--disable-backgrounding-occluded-windows',
                        '--disable-features=TranslateUI,BlinkGenPropertyTrees',
                        f'--user-agent={self.get_random_user_agent()}'
                    ]
                )
                self.root.after(0, lambda: self.append_result("  ✅ Browser launched with stealth mode.\n"))
            except Exception as e:
                raise Exception(f"Failed to launch browser: {str(e)}")
            
            # Create new page with enhanced stealth settings
            try:
                page = browser.new_page()
                
                # Set realistic viewport and screen resolution
                page.set_viewport_size({"width": 1920, "height": 1080})
                
                # Inject enhanced stealth JavaScript
                stealth_script = self.get_enhanced_stealth_script()
                page.add_init_script(stealth_script)
                
                # Special handling for e-commerce sites
                if self.is_ecommerce_site(url):
                    self.root.after(0, lambda: self.append_result("  🛒 E-commerce site detected - applying enhanced stealth...\n"))
                    
                    # Add additional e-commerce specific stealth
                    ecommerce_script = """
                    // E-commerce specific stealth
                    window.localStorage.clear();
                    window.sessionStorage.clear();
                    
                    // Mock realistic browsing history
                    Object.defineProperty(history, 'length', {get: () => 5});
                    
                    // Mock realistic referrer
                    Object.defineProperty(document, 'referrer', {get: () => 'https://www.google.com/'});
                    
                    // Mock realistic document ready state
                    Object.defineProperty(document, 'readyState', {get: () => 'complete'});
                    
                    // Mock realistic performance timing
                    if (window.performance && window.performance.timing) {
                        const now = Date.now();
                        window.performance.timing = {
                            navigationStart: now - 1000,
                            loadEventEnd: now - 100,
                            domContentLoadedEventEnd: now - 200
                        };
                    }
                    """
                    page.add_init_script(ecommerce_script)
                
                # Set realistic headers
                page.set_extra_http_headers({
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                    "Cache-Control": "max-age=0",
                    "DNT": "1"
                })
                
                self.root.after(0, lambda: self.append_result("  ✅ Page created with stealth settings.\n"))
            except Exception as e:
                raise Exception(f"Failed to create page: {str(e)}")
            
            # Add random delay before navigation
            import time
            import random
            delay = random.uniform(2, 5)
            self.root.after(0, lambda: self.append_result(f"  Waiting {delay:.1f}s before navigation...\n"))
            time.sleep(delay)
            
            # Navigate to page with extended timeouts and retry logic
            self.root.after(0, lambda: self.append_result("  Navigating to page...\n"))
            max_retries = 5  # Increased retries
            navigation_success = False
            
            for attempt in range(max_retries):
                try:
                    self.root.after(0, lambda: self.append_result(f"  Attempt {attempt + 1}/{max_retries}...\n"))
                    
                    # Try different wait strategies
                    if attempt == 0:
                        # First attempt: standard navigation
                        page.goto(url, timeout=120000, wait_until="domcontentloaded")
                    elif attempt == 1:
                        # Second attempt: wait for load
                        page.goto(url, timeout=120000, wait_until="load")
                    elif attempt == 2:
                        # Third attempt: wait for network idle
                        page.goto(url, timeout=120000, wait_until="networkidle")
                    else:
                        # Final attempts: no wait condition
                        page.goto(url, timeout=120000)
                    
                    self.root.after(0, lambda: self.append_result(f"  ✅ Page loaded successfully (attempt {attempt + 1})\n"))
                    navigation_success = True
                    break
                    
                except Exception as e:
                    self.root.after(0, lambda: self.append_result(f"  ⚠️ Attempt {attempt + 1} failed: {str(e)[:100]}...\n"))
                    if attempt < max_retries - 1:
                        retry_delay = random.uniform(3, 7)
                        self.root.after(0, lambda: self.append_result(f"  Waiting {retry_delay:.1f}s before retry...\n"))
                        time.sleep(retry_delay)
                    else:
                        raise e
            
            if not navigation_success:
                raise Exception("All navigation attempts failed")
            
            # Comprehensive waiting strategy for dynamic content
            self.root.after(0, lambda: self.append_result("  Waiting for dynamic content to load...\n"))
            
            # Wait for DOM content loaded (increased timeout)
            try:
                page.wait_for_load_state("domcontentloaded", timeout=60000)
                self.root.after(0, lambda: self.append_result("  ✅ DOM content loaded.\n"))
            except Exception:
                self.root.after(0, lambda: self.append_result("  ⚠️ DOM content timeout, continuing...\n"))
            
            # Wait for load event (increased timeout)
            try:
                page.wait_for_load_state("load", timeout=60000)
                self.root.after(0, lambda: self.append_result("  ✅ Load event completed.\n"))
            except Exception:
                self.root.after(0, lambda: self.append_result("  ⚠️ Load event timeout, continuing...\n"))
            
            # Wait for network idle (increased timeout)
            try:
                page.wait_for_load_state("networkidle", timeout=90000)  # 90 seconds
                self.root.after(0, lambda: self.append_result("  ✅ Network idle achieved.\n"))
            except Exception:
                self.root.after(0, lambda: self.append_result("  ⚠️ Network idle timeout, continuing...\n"))
            
            # Extended wait for JavaScript-heavy sites
            wait_time = random.uniform(8, 15)
            self.root.after(0, lambda: self.append_result(f"  Additional wait for dynamic content ({wait_time:.1f} seconds)...\n"))
            time.sleep(wait_time)
            
            # Human-like scrolling behavior
            try:
                self.root.after(0, lambda: self.append_result("  Simulating human-like scrolling...\n"))
                
                # Get page height
                page_height = page.evaluate("document.body.scrollHeight")
                viewport_height = page.viewport_size["height"]
                
                # Scroll down in small increments like a human
                scroll_position = 0
                scroll_increment = random.randint(200, 400)
                
                while scroll_position < page_height:
                    # Random pause between scrolls
                    pause = random.uniform(0.5, 2.0)
                    time.sleep(pause)
                    
                    # Scroll down
                    scroll_position += scroll_increment
                    page.evaluate(f"window.scrollTo(0, {min(scroll_position, page_height)})")
                    
                    # Sometimes scroll back up a bit (human behavior)
                    if random.random() < 0.3:
                        back_scroll = random.randint(50, 150)
                        page.evaluate(f"window.scrollTo(0, {max(0, scroll_position - back_scroll)})")
                        time.sleep(random.uniform(0.3, 1.0))
                
                # Scroll to top
                page.evaluate("window.scrollTo(0, 0)")
                time.sleep(random.uniform(1, 3))
                
                # Random mouse movements (simulate human behavior)
                try:
                    page.mouse.move(random.randint(100, 800), random.randint(100, 600))
                    time.sleep(random.uniform(0.5, 1.5))
                    page.mouse.move(random.randint(100, 800), random.randint(100, 600))
                except:
                    pass
                
                self.root.after(0, lambda: self.append_result("  ✅ Human-like behavior simulation completed.\n"))
            except Exception as e:
                self.root.after(0, lambda: self.append_result(f"  ⚠️ Scrolling simulation failed: {str(e)[:50]}...\n"))
            
            # Extract HTML content
            self.root.after(0, lambda: self.append_result("  Extracting page content...\n"))
            try:
                html_content = page.content()
                self.root.after(0, lambda: self.append_result(f"  ✅ Content extracted ({len(html_content)} characters).\n"))
                
                # Check for captcha or blocking
                if self.detect_captcha_or_blocking(html_content):
                    self.root.after(0, lambda: self.append_result("  ⚠️ Captcha or blocking detected in content!\n"))
                    
                    # Detect captcha type
                    captcha_type = self.detect_captcha_type(html_content)
                    self.root.after(0, lambda: self.append_result(f"  🔍 Detected captcha type: {captcha_type}\n"))
                    
                    captcha_solved = False
                    
                    # Handle Alibaba NoCaptcha slider
                    if captcha_type == "alibaba_nocaptcha":
                        self.root.after(0, lambda: self.append_result("  🎯 Attempting to solve Alibaba NoCaptcha slider...\n"))
                        captcha_solved = self.solve_alibaba_nocaptcha(page, url)
                        
                        if captcha_solved:
                            # Wait and check if page changed
                            time.sleep(3)
                            html_content = page.content()
                            if not self.detect_captcha_or_blocking(html_content):
                                self.root.after(0, lambda: self.append_result("  ✅ Alibaba NoCaptcha solved successfully!\n"))
                            else:
                                self.root.after(0, lambda: self.append_result("  ⚠️ Captcha still present, continuing anyway...\n"))
                    
                    # Try to solve other captcha types with 2Captcha
                    elif self.use_2captcha.get() and self.captcha_api_key.get().strip():
                        self.root.after(0, lambda: self.append_result("  🔐 Attempting to solve captcha with 2Captcha...\n"))
                        
                        # Check for reCAPTCHA v2
                        if captcha_type == "recaptcha_v2":
                            try:
                                # Extract site key
                                site_key = None
                                if 'data-sitekey=' in html_content:
                                    import re
                                    match = re.search(r'data-sitekey="([^"]+)"', html_content)
                                    if match:
                                        site_key = match.group(1)
                                
                                if site_key:
                                    self.root.after(0, lambda: self.append_result(f"  📝 Found reCAPTCHA v2, site key: {site_key}\n"))
                                    solution = self.solve_2captcha("recaptcha_v2", url, site_key)
                                    if solution:
                                        # Inject solution into page
                                        page.evaluate(f"""
                                            document.querySelector('[name="g-recaptcha-response"]').value = '{solution}';
                                            if (typeof grecaptcha !== 'undefined') {{
                                                grecaptcha.getResponse = function() {{ return '{solution}'; }};
                                            }}
                                        """)
                                        captcha_solved = True
                                        self.root.after(0, lambda: self.append_result("  ✅ reCAPTCHA v2 solution injected!\n"))
                            except Exception as e:
                                self.root.after(0, lambda: self.append_result(f"  ❌ reCAPTCHA v2 solving failed: {str(e)}\n"))
                        
                        # Check for hCaptcha
                        elif captcha_type == "hcaptcha":
                            try:
                                # Extract site key
                                site_key = None
                                if 'data-sitekey=' in html_content:
                                    import re
                                    match = re.search(r'data-sitekey="([^"]+)"', html_content)
                                    if match:
                                        site_key = match.group(1)
                                
                                if site_key:
                                    self.root.after(0, lambda: self.append_result(f"  📝 Found hCaptcha, site key: {site_key}\n"))
                                    solution = self.solve_2captcha("hcaptcha", url, site_key)
                                    if solution:
                                        # Inject solution into page
                                        page.evaluate(f"""
                                            document.querySelector('[name="h-captcha-response"]').value = '{solution}';
                                        """)
                                        captcha_solved = True
                                        self.root.after(0, lambda: self.append_result("  ✅ hCaptcha solution injected!\n"))
                            except Exception as e:
                                self.root.after(0, lambda: self.append_result(f"  ❌ hCaptcha solving failed: {str(e)}\n"))
                        
                        # Check for image captcha
                        elif captcha_type == "image_captcha":
                            try:
                                # Try to find captcha image
                                captcha_img = page.query_selector('img[src*="captcha"], img[alt*="captcha"], img[id*="captcha"]')
                                if captcha_img:
                                    # Get image data
                                    img_data = captcha_img.screenshot()
                                    solution = self.solve_2captcha("image", url, None, img_data)
                                    if solution:
                                        # Find input field and enter solution
                                        input_field = page.query_selector('input[name*="captcha"], input[id*="captcha"]')
                                        if input_field:
                                            input_field.fill(solution)
                                            captcha_solved = True
                                            self.root.after(0, lambda: self.append_result("  ✅ Image captcha solution entered!\n"))
                            except Exception as e:
                                self.root.after(0, lambda: self.append_result(f"  ❌ Image captcha solving failed: {str(e)}\n"))
                        
                        if captcha_solved:
                            # Wait a bit and refresh page
                            time.sleep(2)
                            page.reload()
                            time.sleep(3)
                            html_content = page.content()
                            self.root.after(0, lambda: self.append_result("  🔄 Page reloaded after captcha solution\n"))
                        else:
                            self.root.after(0, lambda: self.append_result("  ⚠️ Could not solve captcha automatically\n"))
                    
                    if not captcha_solved:
                        self.root.after(0, lambda: self.append_result("  💡 Recommendations:\n"))
                        if captcha_type == "alibaba_nocaptcha":
                            self.root.after(0, lambda: self.append_result("     • Alibaba NoCaptcha detected - try again with Dynamic mode\n"))
                            self.root.after(0, lambda: self.append_result("     • Enable proxy settings for better success rate\n"))
                            self.root.after(0, lambda: self.append_result("     • Wait 5-10 minutes before retrying\n"))
                        else:
                            self.root.after(0, lambda: self.append_result("     • Enable 2Captcha auto-solving\n"))
                            self.root.after(0, lambda: self.append_result("     • Try using Dynamic scraping mode\n"))
                            self.root.after(0, lambda: self.append_result("     • Enable proxy settings\n"))
                            self.root.after(0, lambda: self.append_result("     • Wait 5-10 minutes before retrying\n"))
                        self.root.after(0, lambda: self.append_result("     • Try a different URL or website\n"))
                        self.root.after(0, lambda: self.append_result("     • Consider using residential proxies\n"))
                
            except Exception as e:
                raise Exception(f"Failed to extract content: {str(e)}")
            
            # Close browser and stop Playwright
            try:
                browser.close()
                playwright_instance.stop()
                self.root.after(0, lambda: self.append_result("  ✅ Browser closed successfully.\n"))
            except Exception as e:
                self.root.after(0, lambda: self.append_result(f"  ⚠️ Cleanup warning: {str(e)}\n"))
            
            # Extract content using all selector types
            self.root.after(0, lambda: self.append_result("  Processing extracted content...\n"))
            results = self.extract_content_dynamic(html_content, url, tag, class_name, id_name, css_selector, xpath_selector)
            self.root.after(0, lambda: self.append_result("  ✅ Content processing completed.\n"))
            
            return results, html_content
                
        except Exception as e:
            # Comprehensive cleanup
            if page:
                try:
                    page.close()
                except:
                    pass
            if browser:
                try:
                    browser.close()
                except:
                    pass
            if playwright_instance:
                try:
                    playwright_instance.stop()
                except:
                    pass
            
            error_msg = f"Dynamic scraping failed: {str(e)}"
            self.root.after(0, lambda: self.append_result(f"  ❌ {error_msg}\n"))
            raise Exception(error_msg)
    
    def extract_content_dynamic(self, html_content, base_url, tag=None, class_name=None, id_name=None, css_selector=None, xpath_selector=None):
        """Enhanced content extraction for dynamic scraping with image support"""
        results = {}
        soup = BeautifulSoup(html_content, "html.parser")
        
        # HTML Tag extraction
        if tag:
            self.root.after(0, lambda: self.append_result(f"\nResults for HTML tag <{tag}>:\n"))
            elements = soup.find_all(tag)
            results['tag'] = []
            
            for i, element in enumerate(elements[:10]):
                if element.name == 'img':
                    # Handle image elements
                    img_url = self.get_image_url(element, base_url)
                    if img_url:
                        results['tag'].append(f"[IMAGE] {img_url}")
                        self.root.after(0, lambda url=img_url: self.append_result(f"  [IMAGE] {url}\n"))
                        self.root.after(0, lambda url=img_url: self.display_image_in_log(url))
                    else:
                        results['tag'].append("[IMAGE] No source found")
                        self.root.after(0, lambda: self.append_result("  [IMAGE] No source found\n"))
                else:
                    # Handle text elements
                    text = element.get_text(strip=True)
                    if text:
                        results['tag'].append(text)
                        self.root.after(0, lambda t=text: self.append_result(f"  {t}\n"))
                    
                    # Find images within this element
                    self.extract_images_from_element(element, base_url, results, 'tag')
        
        # CSS Class extraction
        if class_name:
            self.root.after(0, lambda: self.append_result(f"\nResults for CSS class '{class_name}':\n"))
            elements = soup.find_all(class_=class_name)
            results['class'] = []
            
            for element in elements[:10]:
                if element.name == 'img':
                    # Handle direct image elements
                    img_url = self.get_image_url(element, base_url)
                    if img_url:
                        results['class'].append(f"[IMAGE] {img_url}")
                        self.root.after(0, lambda url=img_url: self.append_result(f"  [IMAGE] {url}\n"))
                        self.root.after(0, lambda url=img_url: self.display_image_in_log(url))
                else:
                    # Handle container elements
                    text = element.get_text(strip=True)
                    if text:
                        results['class'].append(text)
                        self.root.after(0, lambda t=text: self.append_result(f"  {t}\n"))
                    
                    # Find images within this element
                    self.extract_images_from_element(element, base_url, results, 'class')
        
        # Element ID extraction
        if id_name:
            self.root.after(0, lambda: self.append_result(f"\nResults for element ID '{id_name}':\n"))
            element = soup.find(id=id_name)
            results['id'] = []
            
            if element:
                if element.name == 'img':
                    # Handle direct image element
                    img_url = self.get_image_url(element, base_url)
                    if img_url:
                        results['id'].append(f"[IMAGE] {img_url}")
                        self.root.after(0, lambda url=img_url: self.append_result(f"  [IMAGE] {url}\n"))
                        self.root.after(0, lambda url=img_url: self.display_image_in_log(url))
                else:
                    # Handle container element
                    text = element.get_text(strip=True)
                    if text:
                        results['id'].append(text)
                        self.root.after(0, lambda t=text: self.append_result(f"  {t}\n"))
                    
                    # Find images within this element
                    self.extract_images_from_element(element, base_url, results, 'id')
            else:
                self.root.after(0, lambda: self.append_result("  No element found\n"))
        
        # CSS Selector extraction
        if css_selector:
            self.root.after(0, lambda: self.append_result(f"\nResults for CSS selector '{css_selector}':\n"))
            try:
                elements = soup.select(css_selector)
                results['css'] = []
                
                for element in elements[:10]:
                    if element.name == 'img':
                        # Handle direct image elements
                        img_url = self.get_image_url(element, base_url)
                        if img_url:
                            results['css'].append(f"[IMAGE] {img_url}")
                            self.root.after(0, lambda url=img_url: self.append_result(f"  [IMAGE] {url}\n"))
                            self.root.after(0, lambda url=img_url: self.display_image_in_log(url))
                    else:
                        # Handle container elements
                        text = element.get_text(strip=True)
                        if text:
                            results['css'].append(text)
                            self.root.after(0, lambda t=text: self.append_result(f"  {t}\n"))
                        
                        # Find images within this element
                        self.extract_images_from_element(element, base_url, results, 'css')
            except Exception as e:
                self.root.after(0, lambda: self.append_result(f"  CSS selector error: {str(e)}\n"))
        
        # XPath extraction
        if xpath_selector:
            self.root.after(0, lambda: self.append_result(f"\nResults for XPath '{xpath_selector}':\n"))
            try:
                tree = html.fromstring(html_content)
                xpath_results = tree.xpath(xpath_selector)
                results['xpath'] = []
                
                for r in xpath_results[:10]:
                    if hasattr(r, "text_content"):
                        text = r.text_content().strip()
                        if text:
                            results['xpath'].append(text)
                            self.root.after(0, lambda t=text: self.append_result(f"  {t}\n"))
                        
                        # Find images within XPath results
                        try:
                            element_html = html.tostring(r, encoding='unicode')
                            element_soup = BeautifulSoup(element_html, 'html.parser')
                            self.extract_images_from_element(element_soup, base_url, results, 'xpath')
                        except:
                            pass
                    else:
                        text = str(r).strip()
                        if text:
                            results['xpath'].append(text)
                            self.root.after(0, lambda t=text: self.append_result(f"  {t}\n"))
            except Exception as e:
                self.root.after(0, lambda: self.append_result(f"  XPath error: {str(e)}\n"))
        
        return results
    
    def get_image_url(self, img_element, base_url):
        """Get image URL from img element"""
        img_url = img_element.get('src') or img_element.get('data-src') or img_element.get('data-lazy-src') or img_element.get('data-original')
        if img_url:
            # Convert relative URL to absolute
            if not img_url.startswith(('http://', 'https://')):
                img_url = urljoin(base_url, img_url)
        return img_url
    
    def extract_images_from_element(self, element, base_url, results, result_type):
        """Extract images from within an element"""
        images = element.find_all('img')
        for img in images:
            img_url = self.get_image_url(img, base_url)
            if img_url:
                results[result_type].append(f"[IMAGE] {img_url}")
                self.root.after(0, lambda url=img_url: self.append_result(f"  [IMAGE] {url}\n"))
                self.root.after(0, lambda url=img_url: self.display_image_in_log(url))
    
    def extract_content(self, html_content, tag=None, class_name=None, id_name=None, css_selector=None, xpath_selector=None):
        """Extract content using various selectors"""
        results = {}
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Tag extraction
        if tag:
            elements = soup.find_all(tag)
            results['tag'] = []
            self.root.after(0, lambda: self.append_result(f"Results for tag <{tag}>:\n"))
            for e in elements[:10]:
                if e.name == 'img':
                    # Handle image elements
                    img_url = e.get('src') or e.get('data-src') or e.get('data-lazy-src')
                    if img_url:
                        results['tag'].append(f"[IMAGE] {img_url}")
                        self.root.after(0, lambda url=img_url: self.append_result(f"  [IMAGE] {url}\n"))
                        self.root.after(0, lambda url=img_url: self.display_image_in_log(url))
                    else:
                        results['tag'].append("[IMAGE] No source found")
                        self.root.after(0, lambda: self.append_result("  [IMAGE] No source found\n"))
                else:
                    text = e.get_text(strip=True)
                    results['tag'].append(text)
                    self.root.after(0, lambda t=text: self.append_result(f"  {t}\n"))
        
        # Class extraction
        if class_name:
            elements = soup.find_all(class_=class_name)
            results['class'] = []
            self.root.after(0, lambda: self.append_result(f"\nResults for class='{class_name}':\n"))
            for e in elements[:10]:
                if e.name == 'img':
                    # Handle direct image elements
                    img_url = e.get('src') or e.get('data-src') or e.get('data-lazy-src')
                    if img_url:
                        results['class'].append(f"[IMAGE] {img_url}")
                        self.root.after(0, lambda url=img_url: self.append_result(f"  [IMAGE] {url}\n"))
                        self.root.after(0, lambda url=img_url: self.display_image_in_log(url))
                    else:
                        results['class'].append("[IMAGE] No source found")
                        self.root.after(0, lambda: self.append_result("  [IMAGE] No source found\n"))
                else:
                    # Handle container elements - extract text and images
                    text = e.get_text(strip=True)
                    if text:
                        results['class'].append(text)
                        self.root.after(0, lambda t=text: self.append_result(f"  {t}\n"))
                    
                    # Find images within this element
                    images = e.find_all('img')
                    for img in images:
                        img_url = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                        if img_url:
                            results['class'].append(f"[IMAGE] {img_url}")
                            self.root.after(0, lambda url=img_url: self.append_result(f"  [IMAGE] {url}\n"))
                            self.root.after(0, lambda url=img_url: self.display_image_in_log(url))
        
        # ID extraction
        if id_name:
            element = soup.find(id=id_name)
            if element:
                results['id'] = []
                self.root.after(0, lambda: self.append_result(f"\nResults for id='{id_name}':\n"))
                
                if element.name == 'img':
                    # Handle direct image element
                    img_url = element.get('src') or element.get('data-src') or element.get('data-lazy-src')
                    if img_url:
                        results['id'].append(f"[IMAGE] {img_url}")
                        self.root.after(0, lambda url=img_url: self.append_result(f"  [IMAGE] {url}\n"))
                        self.root.after(0, lambda url=img_url: self.display_image_in_log(url))
                    else:
                        results['id'].append("[IMAGE] No source found")
                        self.root.after(0, lambda: self.append_result("  [IMAGE] No source found\n"))
                else:
                    # Handle container element - extract text and images
                    text = element.get_text(strip=True)
                    if text:
                        results['id'].append(text)
                        self.root.after(0, lambda t=text: self.append_result(f"  {t}\n"))
                    
                    # Find images within this element
                    images = element.find_all('img')
                    for img in images:
                        img_url = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                        if img_url:
                            results['id'].append(f"[IMAGE] {img_url}")
                            self.root.after(0, lambda url=img_url: self.append_result(f"  [IMAGE] {url}\n"))
                            self.root.after(0, lambda url=img_url: self.display_image_in_log(url))
            else:
                results['id'] = []
                self.root.after(0, lambda: self.append_result(f"\nResults for id='{id_name}':\n"))
                self.root.after(0, lambda: self.append_result("  No element found\n"))
        
        # CSS selector extraction
        if css_selector:
            elements = soup.select(css_selector)
            results['css'] = []
            self.root.after(0, lambda: self.append_result(f"\nResults for CSS selector '{css_selector}':\n"))
            for e in elements[:10]:
                if e.name == 'img':
                    # Handle direct image elements
                    img_url = e.get('src') or e.get('data-src') or e.get('data-lazy-src')
                    if img_url:
                        results['css'].append(f"[IMAGE] {img_url}")
                        self.root.after(0, lambda url=img_url: self.append_result(f"  [IMAGE] {url}\n"))
                        self.root.after(0, lambda url=img_url: self.display_image_in_log(url))
                    else:
                        results['css'].append("[IMAGE] No source found")
                        self.root.after(0, lambda: self.append_result("  [IMAGE] No source found\n"))
                else:
                    # Handle container elements - extract text and images
                    text = e.get_text(strip=True)
                    if text:
                        results['css'].append(text)
                        self.root.after(0, lambda t=text: self.append_result(f"  {t}\n"))
                    
                    # Find images within this element
                    images = e.find_all('img')
                    for img in images:
                        img_url = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                        if img_url:
                            results['css'].append(f"[IMAGE] {img_url}")
                            self.root.after(0, lambda url=img_url: self.append_result(f"  [IMAGE] {url}\n"))
                            self.root.after(0, lambda url=img_url: self.display_image_in_log(url))
        
        # XPath extraction
        if xpath_selector:
            tree = html.fromstring(html_content)
            xpath_results = tree.xpath(xpath_selector)
            results['xpath'] = []
            self.root.after(0, lambda: self.append_result(f"\nResults for XPath '{xpath_selector}':\n"))
            for r in xpath_results[:10]:
                if hasattr(r, "text_content"):
                    text = r.text_content().strip()
                    if text:
                        results['xpath'].append(text)
                        self.root.after(0, lambda t=text: self.append_result(f"  {t}\n"))
                    
                    # Find images within this element
                    if hasattr(r, 'xpath'):
                        try:
                            # Convert lxml element back to BeautifulSoup for image search
                            element_html = html.tostring(r, encoding='unicode')
                            element_soup = BeautifulSoup(element_html, 'html.parser')
                            images = element_soup.find_all('img')
                            for img in images:
                                img_url = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                                if img_url:
                                    results['xpath'].append(f"[IMAGE] {img_url}")
                                    self.root.after(0, lambda url=img_url: self.append_result(f"  [IMAGE] {url}\n"))
                                    self.root.after(0, lambda url=img_url: self.display_image_in_log(url))
                        except:
                            pass
                else:
                    text = str(r).strip()
                    if text:
                        results['xpath'].append(text)
                        self.root.after(0, lambda t=text: self.append_result(f"  {t}\n"))
        
        return results
    
    def display_image_in_log(self, img_url):
        """Display image in the log/results area with download functionality"""
        try:
            img_data = None
            content_type = ""
            
            # Handle data URLs (base64 encoded images)
            if img_url.startswith('data:'):
                try:
                    # Parse data URL: data:image/png;base64,iVBORw0KGgo...
                    header, data = img_url.split(',', 1)
                    if ';base64' in header:
                        content_type = header.split(':')[1].split(';')[0]
                        img_data = base64.b64decode(data)
                        self.append_result(f"    [Base64 Image: {content_type}]\n")
                    else:
                        self.append_result("    [Unsupported data URL format]\n")
                        return
                except Exception as e:
                    self.append_result(f"    [Error parsing data URL: {str(e)}]\n")
                    return
            else:
                # Handle regular URLs
                # Convert relative URL to absolute if needed
                if not img_url.startswith(('http://', 'https://')):
                    base_url = self.url_var.get().strip()
                    img_url = urljoin(base_url, img_url)
                
                # Download image
                response = requests.get(img_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                response.raise_for_status()
                
                # Check if it's actually an image
                content_type = response.headers.get('content-type', '')
                if not content_type.startswith('image/'):
                    self.append_result("    [Not a valid image]\n")
                    return
                
                img_data = response.content
            
            # Load and resize image
            img_pil = Image.open(io.BytesIO(img_data))
            original_width, original_height = img_pil.size
            
            # Resize to fit in log (max 200x150)
            max_width, max_height = 200, 150
            
            if original_width > max_width or original_height > max_height:
                ratio = min(max_width/original_width, max_height/original_height)
                new_width = int(original_width * ratio)
                new_height = int(original_height * ratio)
                img_pil = img_pil.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            img_tk = ImageTk.PhotoImage(img_pil)
            
            # Insert image into text widget
            self.results_text.image_create(tk.END, image=img_tk)
            self.results_text.insert(tk.END, "\n")
            
            # Keep a reference to prevent garbage collection
            if not hasattr(self, 'image_references'):
                self.image_references = []
            self.image_references.append(img_tk)
            
            # Store image data for download
            if not hasattr(self, 'image_data'):
                self.image_data = []
            self.image_data.append({
                'url': img_url,
                'content': img_data,
                'original_size': (original_width, original_height),
                'file_size': len(img_data),
                'content_type': content_type
            })
            
            # Add image info with download button
            self.append_result(f"    Size: {original_width}x{original_height} | File size: {len(img_data)} bytes\n")
            self.append_result("    [Click 'Download Image' button below to save this image]\n")
            
            # Add download button
            self.add_download_button(img_url, len(self.image_data) - 1)
            
        except Exception as e:
            self.append_result(f"    [Error loading image: {str(e)}]\n")
    
    def add_download_button(self, img_url, image_index):
        """Add a download button for the image"""
        try:
            # Create a frame for the download button
            button_frame = tk.Frame(self.results_text)
            self.results_text.window_create(tk.END, window=button_frame)
            
            # Create download button
            download_btn = tk.Button(
                button_frame, 
                text="📥 画像をダウンロード", 
                command=lambda: self.download_image(image_index),
                bg='#4CAF50',
                fg='white',
                font=('Arial', 8),
                relief='raised',
                bd=2
            )
            download_btn.pack(pady=2)
            
            # Add some spacing
            self.results_text.insert(tk.END, "\n")
            
        except Exception as e:
            self.append_result(f"    [ボタン追加エラー: {str(e)}]\n")
    
    def download_image(self, image_index):
        """Download the image to user's chosen location"""
        try:
            if not hasattr(self, 'image_data') or image_index >= len(self.image_data):
                messagebox.showerror("エラー", "画像データが見つかりません")
                return
            
            image_info = self.image_data[image_index]
            img_url = image_info['url']
            content = image_info['content']
            
            # Get filename from URL or create one for data URLs
            if img_url.startswith('data:'):
                # For data URLs, create filename based on content type
                content_type = image_info['content_type']
                if 'jpeg' in content_type or 'jpg' in content_type:
                    ext = '.jpg'
                elif 'png' in content_type:
                    ext = '.png'
                elif 'gif' in content_type:
                    ext = '.gif'
                elif 'webp' in content_type:
                    ext = '.webp'
                else:
                    ext = '.png'  # Default for base64 images
                filename = f"base64_image_{image_index + 1}{ext}"
            else:
                # For regular URLs
                parsed_url = urlparse(img_url)
                filename = os.path.basename(parsed_url.path)
                
                # If no filename or extension, create one
                if not filename or '.' not in filename:
                    # Determine extension from content type
                    content_type = image_info['content_type']
                    if 'jpeg' in content_type or 'jpg' in content_type:
                        ext = '.jpg'
                    elif 'png' in content_type:
                        ext = '.png'
                    elif 'gif' in content_type:
                        ext = '.gif'
                    elif 'webp' in content_type:
                        ext = '.webp'
                    else:
                        ext = '.jpg'
                    filename = f"downloaded_image_{image_index + 1}{ext}"
            
            # Ask user where to save
            file_path = filedialog.asksaveasfilename(
                defaultextension=os.path.splitext(filename)[1],
                initialfile=filename,
                filetypes=[
                    ("すべてのファイル", "*.*"),
                    ("JPEG ファイル", "*.jpg"),
                    ("PNG ファイル", "*.png"),
                    ("GIF ファイル", "*.gif"),
                    ("WebP ファイル", "*.webp")
                ]
            )
            
            if file_path:
                # Save the image
                with open(file_path, 'wb') as f:
                    f.write(content)
                
                # Show success message
                messagebox.showinfo("成功", f"画像を保存しました:\n{file_path}")
                self.append_result(f"    ✅ 画像を保存しました: {file_path}\n")
                
        except Exception as e:
            messagebox.showerror("エラー", f"画像のダウンロードに失敗しました:\n{str(e)}")
            self.append_result(f"    ❌ ダウンロード失敗: {str(e)}\n")
    
    def install_playwright(self):
        """Install Playwright browsers"""
        try:
            import subprocess
            import sys
            
            self.append_result("Playwright のブラウザをインストールしています...\n")
            self.append_result("数分かかる場合があります...\n")
            
            # Run the installation command
            result = subprocess.run([
                sys.executable, "-m", "playwright", "install", "chromium"
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.append_result("✅ Playwright のブラウザを正常にインストールしました！\n")
                self.append_result("Dynamic モードが使用可能になりました。\n")
                messagebox.showinfo("成功", "Playwright のブラウザをインストールしました。\nDynamic モードが使用可能です。")
            else:
                error_msg = result.stderr or result.stdout
                self.append_result(f"❌ インストールに失敗しました: {error_msg}\n")
                messagebox.showerror("インストール失敗", f"Playwright のインストールに失敗しました:\n{error_msg}")
                
        except subprocess.TimeoutExpired:
            self.append_result("❌ インストールがタイムアウトしました。もう一度お試しください。\n")
            messagebox.showerror("タイムアウト", "インストールがタイムアウトしました。もう一度お試しください。")
        except Exception as e:
            self.append_result(f"❌ インストールエラー: {str(e)}\n")
            messagebox.showerror("エラー", f"Playwright のインストールに失敗しました:\n{str(e)}")
    
    def append_result(self, text):
        """Append text to results area"""
        self.results_text.insert(tk.END, text)
        self.results_text.see(tk.END)
    
    def scraping_complete(self, results):
        """Called when scraping is complete"""
        self.scraping_results = results
        self.progress.stop()
        self.scrape_btn.config(state='normal')
        self.pause_btn.config(state='disabled', text="一時停止")
        self.stop_btn.config(state='disabled')
        self.is_paused = False
        self.should_stop = False
        self.append_result("\n" + "="*50 + "\nスクレイピングが正常に完了しました！\n")
    
    def scraping_error(self, error_msg):
        """Called when scraping encounters an error"""
        self.progress.stop()
        self.scrape_btn.config(state='normal')
        self.pause_btn.config(state='disabled', text="一時停止")
        self.stop_btn.config(state='disabled')
        self.is_paused = False
        self.should_stop = False
        self.append_result(f"\nエラー: {error_msg}\n")
        messagebox.showerror("スクレイピングエラー", f"エラーが発生しました:\n{error_msg}")
    
    def clear_results(self):
        """Clear the results area"""
        self.results_text.delete(1.0, tk.END)
        self.scraping_results = {}
        # Clear image references and data
        if hasattr(self, 'image_references'):
            self.image_references = []
        if hasattr(self, 'image_data'):
            self.image_data = []
    
    def save_results(self):
        """Save results to file"""
        if not self.scraping_results:
            messagebox.showwarning("警告", "保存する結果がありません")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON ファイル", "*.json"), ("CSV ファイル", "*.csv"), ("テキスト ファイル", "*.txt")]
        )
        
        if file_path:
            try:
                if file_path.endswith('.json'):
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(self.scraping_results, f, indent=2, ensure_ascii=False)
                elif file_path.endswith('.csv'):
                    with open(file_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow(['Selector Type', 'Content'])
                        for selector_type, content_list in self.scraping_results.items():
                            for content in content_list:
                                writer.writerow([selector_type, content])
                else:  # txt
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(self.results_text.get(1.0, tk.END))
                
                messagebox.showinfo("成功", f"結果を保存しました: {file_path}")
            except Exception as e:
                messagebox.showerror("エラー", f"ファイルの保存に失敗しました:\n{str(e)}")


def main():
    root = tk.Tk()
    app = WebScraperGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
