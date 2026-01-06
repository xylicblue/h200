#!/usr/bin/env python3
"""
Prime Intellect H200 GPU Price Scraper
Extracts H200 pricing from Prime Intellect

Prime Intellect offers H200 GPUs with Spot and Secure pricing.
This scraper uses the Spot price as the primary price.

Reference: https://app.primeintellect.ai/dashboard/create-cluster
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import time
from typing import Dict, Optional


class PrimeIntellectH200Scraper:
    """Scraper for Prime Intellect H200 GPU pricing"""
    
    def __init__(self):
        self.name = "PrimeIntellect"
        self.base_url = "https://app.primeintellect.ai/dashboard/create-cluster?gpu_type=H200_141GB&image=ubuntu_22_cuda_12&location=Cheapest&pricing_type=Cheapest&quantity=1&security=Cheapest"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
    
    def get_h200_prices(self) -> Dict[str, str]:
        """Main method to extract H200 prices from Prime Intellect"""
        print(f"🔍 Fetching {self.name} H200 pricing...")
        print("=" * 80)
        
        h200_prices = {}
        
        # Prioritize Selenium since page is JS-heavy (React app)
        methods = [
            ("Selenium Scraper", self._try_selenium_scraper),
            ("Prime Intellect Website Scraping", self._try_pricing_page),
        ]
        
        for method_name, method_func in methods:
            print(f"\n📋 Method: {method_name}")
            try:
                prices = method_func()
                if prices and self._validate_prices(prices):
                    h200_prices.update(prices)
                    print(f"   ✅ Found H200 prices!")
                    break
                else:
                    print(f"   ❌ No valid prices found")
            except Exception as e:
                print(f"   ⚠️  Error: {str(e)[:100]}")
                continue
        
        if not h200_prices:
            print("\n❌ Failed to extract H200 pricing from Prime Intellect")
            return {}
        
        print(f"\n✅ Final extraction complete")
        return h200_prices
    
    def _validate_prices(self, prices: Dict[str, str]) -> bool:
        """Validate that prices are in a reasonable range"""
        if not prices:
            return False
        
        for variant, price_str in prices.items():
            if 'Error' in variant or variant.startswith('_'):
                continue
            try:
                price_match = re.search(r'\$?([0-9.]+)', str(price_str))
                if price_match:
                    price = float(price_match.group(1))
                    # Prime Intellect H200 pricing is around $1-5/hr
                    if 0.5 < price < 10.0:
                        return True
            except:
                continue
        return False
    
    def _try_pricing_page(self) -> Dict[str, str]:
        """Scrape Prime Intellect website for H200 pricing (likely won't work due to JS)"""
        h200_prices = {}
        
        try:
            print(f"    Trying: {self.base_url}")
            response = requests.get(self.base_url, headers=self.headers, timeout=20)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                text_content = soup.get_text()
                
                print(f"      Content length: {len(text_content)}")
                
                # This is a React app, so static scraping likely won't work
                if 'H200' not in text_content:
                    print(f"      ⚠️  No H200 content found (page is likely JS-rendered)")
                    return h200_prices
                
                print(f"      ✓ Found H200 content")
                
                # Extract prices
                prices = self._extract_prices(soup, text_content)
                if prices:
                    h200_prices.update(prices)
                    
            else:
                print(f"      Status {response.status_code}")
                
        except Exception as e:
            print(f"      Error: {str(e)[:50]}...")
        
        return h200_prices
    
    def _extract_prices(self, soup: BeautifulSoup, text_content: str) -> Dict[str, str]:
        """Extract H200 prices from page content"""
        prices = {}
        
        # Look for Spot price pattern
        spot_pattern = r'Spot\s*\$([0-9.]+)'
        spot_match = re.search(spot_pattern, text_content, re.IGNORECASE)
        
        if spot_match:
            spot_price = float(spot_match.group(1))
            if 0.5 < spot_price < 10.0:
                print(f"        ✓ Found Spot price: ${spot_price:.2f}/hr")
                prices["H200 SXM5 Spot (PrimeIntellect)"] = f"${spot_price:.2f}/hr"
        
        # Look for Secure price pattern
        secure_pattern = r'Secure\s*\$([0-9.]+)'
        secure_match = re.search(secure_pattern, text_content, re.IGNORECASE)
        
        if secure_match:
            secure_price = float(secure_match.group(1))
            prices["_secure_price"] = secure_price
        
        return prices
    
    def _try_selenium_scraper(self) -> Dict[str, str]:
        """Use Selenium to scrape JavaScript-loaded pricing from Prime Intellect"""
        h200_prices = {}
        
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            print("    Setting up Selenium WebDriver...")
            
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            driver = webdriver.Chrome(options=chrome_options)
            
            try:
                print(f"    Loading Prime Intellect dashboard...")
                driver.get(self.base_url)
                
                print("    Waiting for dynamic content to load (20s for React)...")
                time.sleep(20)  # Much longer wait for React app to fully load prices
                
                # Use JavaScript to extract H200 pricing - handles React delayed rendering
                script = """
                    const bodyText = document.body.innerText;
                    
                    // Look for H200 section
                    if (!bodyText.includes('H200')) {
                        return { error: 'H200 not found on page' };
                    }
                    
                    // Find spot price - handle "$ 1.55" format with optional space
                    const spotPatterns = [
                        /Spot\\s*\\$\\s*([0-9.]+)/i,
                        /Spot[^\\$]*\\$\\s*([0-9.]+)/i
                    ];
                    const securePatterns = [
                        /Secure\\s*\\$\\s*([0-9.]+)/i,
                        /Secure[^\\$]*\\$\\s*([0-9.]+)/i
                    ];
                    
                    let spotPrice = null;
                    let securePrice = null;
                    
                    for (const pattern of spotPatterns) {
                        const match = bodyText.match(pattern);
                        if (match) {
                            spotPrice = match[1];
                            break;
                        }
                    }
                    
                    for (const pattern of securePatterns) {
                        const match = bodyText.match(pattern);
                        if (match) {
                            securePrice = match[1];
                            break;
                        }
                    }
                    
                    // Also try to find buttons with prices
                    const buttons = document.querySelectorAll('button');
                    buttons.forEach(btn => {
                        const text = btn.innerText;
                        // Handle "Spot $ 1.55" format
                        if (text.includes('Spot') && text.includes('$')) {
                            const match = text.match(/\\$\\s*([0-9.]+)/);
                            if (match && !spotPrice) spotPrice = match[1];
                        }
                        if (text.includes('Secure') && text.includes('$')) {
                            const match = text.match(/\\$\\s*([0-9.]+)/);
                            if (match && !securePrice) securePrice = match[1];
                        }
                    });
                    
                    // Find H200 card and get prices from it
                    if (!spotPrice) {
                        const allDivs = Array.from(document.querySelectorAll('div'));
                        const h200Card = allDivs.find(d => 
                            d.innerText.includes('H200') && 
                            d.innerText.includes('Spot') && 
                            d.innerText.includes('$')
                        );
                        if (h200Card) {
                            const cardText = h200Card.innerText;
                            const allPrices = cardText.match(/\\$\\s*([0-9.]+)/g);
                            if (allPrices && allPrices.length >= 2) {
                                // First price is usually spot (cheaper)
                                const p1 = parseFloat(allPrices[0].replace(/\\$\\s*/, ''));
                                const p2 = parseFloat(allPrices[1].replace(/\\$\\s*/, ''));
                                spotPrice = Math.min(p1, p2).toString();
                                securePrice = Math.max(p1, p2).toString();
                            }
                        }
                    }
                    
                    return {
                        spotPrice: spotPrice,
                        securePrice: securePrice,
                        pageContainsH200: bodyText.includes('H200'),
                        debug: bodyText.substring(0, 500)
                    };
                """
                
                result = driver.execute_script(script)
                
                if result and not result.get('error'):
                    spot_price = None
                    secure_price = None
                    
                    if result.get('spotPrice'):
                        spot_price = float(result['spotPrice'])
                    if result.get('securePrice'):
                        secure_price = float(result['securePrice'])
                    
                    if spot_price and 0.5 < spot_price < 10.0:
                        h200_prices["H200 SXM5 Spot (PrimeIntellect)"] = f"${spot_price:.2f}/hr"
                        h200_prices["_secure_price"] = secure_price
                        
                        print(f"    ✓ Spot: ${spot_price:.2f}/hr")
                        if secure_price:
                            print(f"    ✓ Secure: ${secure_price:.2f}/hr")
                else:
                    print(f"    ⚠️  {result.get('error', 'Could not find H200 pricing')}")
                    
                    # Fallback to BeautifulSoup
                    page_source = driver.page_source
                    soup = BeautifulSoup(page_source, 'html.parser')
                    prices = self._extract_prices(soup, soup.get_text())
                    if prices:
                        h200_prices.update(prices)
                
            finally:
                driver.quit()
                print("    WebDriver closed")
                
        except ImportError:
            print("      ⚠️  Selenium not installed. Run: pip install selenium")
        except Exception as e:
            print(f"      ⚠️  Error: {str(e)[:100]}")
        
        return h200_prices
    
    def save_to_json(self, prices: Dict[str, str], filename: str = "primeintellect_h200_prices.json") -> bool:
        """Save results to a JSON file"""
        try:
            # Extract values
            spot_price = 0.0
            secure_price = None
            
            for key, value in prices.items():
                if key == "_secure_price":
                    secure_price = value
                elif not key.startswith("_"):
                    price_match = re.search(r'\$([0-9.]+)', str(value))
                    if price_match:
                        spot_price = float(price_match.group(1))
            
            output_data = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "provider": self.name,
                "providers": {
                    "PrimeIntellect": {
                        "name": "Prime Intellect",
                        "url": self.base_url,
                        "variants": {
                            "H200 SXM5 Spot (PrimeIntellect)": {
                                "gpu_model": "H200",
                                "gpu_memory": "141GB",
                                "price_per_hour": round(spot_price, 2),
                                "currency": "USD",
                                "availability": "spot"
                            }
                        }
                    }
                },
                "notes": {
                    "instance_type": "Spot Instance",
                    "gpu_model": "NVIDIA H200 SXM5",
                    "gpu_memory": "141GB",
                    "gpu_count_per_instance": 1,
                    "pricing_type": "Spot",
                    "spot_price": round(spot_price, 2),
                    "secure_price": round(secure_price, 2) if secure_price else None,
                    "source": "https://app.primeintellect.ai/dashboard/create-cluster"
                }
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Results saved to: {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving to file: {str(e)}")
            return False


def main():
    """Main function to run the Prime Intellect H200 scraper"""
    print("🚀 Prime Intellect H200 GPU Pricing Scraper")
    print("=" * 80)
    print("Note: Prime Intellect offers Spot and Secure pricing (using Spot price)")
    print("=" * 80)
    
    scraper = PrimeIntellectH200Scraper()
    
    start_time = time.time()
    prices = scraper.get_h200_prices()
    end_time = time.time()
    
    print(f"\n⏱️  Scraping completed in {end_time - start_time:.2f} seconds")
    
    # Display results
    if prices:
        print(f"\n✅ Successfully extracted H200 pricing:\n")
        
        for variant, price in sorted(prices.items()):
            if not variant.startswith('_'):
                print(f"  • {variant:50s} {price}")
        
        # Save results to JSON
        scraper.save_to_json(prices)
    else:
        print("\n❌ No valid pricing data found")


if __name__ == "__main__":
    main()
