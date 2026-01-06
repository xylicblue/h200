#!/usr/bin/env python3
"""
Akash Network H200 GPU Price Scraper
Extracts H200 pricing from Akash Network decentralized cloud

Akash offers H200 GPUs with variable pricing (min/max/average).

Reference: https://akash.network/pricing/gpus/
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import time
from typing import Dict, Optional


class AkashH200Scraper:
    """Scraper for Akash Network H200 GPU pricing"""
    
    def __init__(self):
        self.name = "Akash"
        self.base_url = "https://akash.network/pricing/gpus/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
    
    def get_h200_prices(self) -> Dict[str, str]:
        """Main method to extract H200 prices from Akash Network"""
        print(f"🔍 Fetching {self.name} H200 pricing...")
        print("=" * 80)
        
        h200_prices = {}
        
        # Try multiple methods - prioritize Selenium since page is JS-heavy
        methods = [
            ("Selenium Scraper", self._try_selenium_scraper),
            ("Akash Website Scraping", self._try_pricing_page),
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
            print("\n❌ Failed to extract H200 pricing from Akash Network")
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
                    # Akash H200 pricing is around $2-5/hr
                    if 1.0 < price < 10.0:
                        return True
            except:
                continue
        return False
    
    def _try_pricing_page(self) -> Dict[str, str]:
        """Scrape Akash website for H200 pricing"""
        h200_prices = {}
        
        try:
            print(f"    Trying: {self.base_url}")
            response = requests.get(self.base_url, headers=self.headers, timeout=20)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                text_content = soup.get_text()
                
                print(f"      Content length: {len(text_content)}")
                
                # Check if page contains H200 data
                if 'h200' not in text_content.lower() and 'H200' not in text_content:
                    print(f"      ⚠️  No H200 content found")
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
        
        # Look for H200 section with price patterns
        # Pattern: h200 ... $X.XX
        h200_pattern = r'h200[\s\S]{0,200}\$([0-9.]+)'
        matches = re.findall(h200_pattern, text_content, re.IGNORECASE)
        
        if matches:
            # Get the last price found (usually the average)
            for price_str in reversed(matches):
                try:
                    price = float(price_str)
                    if 1.0 < price < 10.0:
                        print(f"        ✓ Found H200 price: ${price:.2f}/hr")
                        prices["H200 SXM5 (Akash)"] = f"${price:.2f}/hr"
                        return prices
                except ValueError:
                    continue
        
        # Try finding by table structure
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                row_text = row.get_text().lower()
                if 'h200' in row_text:
                    cells = row.find_all(['td', 'th'])
                    for cell in cells:
                        cell_text = cell.get_text()
                        price_match = re.search(r'\$([0-9.]+)', cell_text)
                        if price_match:
                            price = float(price_match.group(1))
                            if 1.0 < price < 10.0:
                                print(f"        ✓ Found H200 price in table: ${price:.2f}/hr")
                                prices["H200 SXM5 (Akash)"] = f"${price:.2f}/hr"
                                return prices
        
        return prices
    
    def _try_selenium_scraper(self) -> Dict[str, str]:
        """Use Selenium to scrape JavaScript-loaded pricing from Akash"""
        h200_prices = {}
        
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            
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
                print(f"    Loading Akash Network page...")
                driver.get(self.base_url)
                
                print("    Waiting for dynamic content to load...")
                time.sleep(10)  # Longer wait for dynamic content
                
                # Use JavaScript to extract H200 pricing - handles div-based layout
                script = """
                    // Find H200 row by the rent button ID
                    const rentButton = document.getElementById('h200-(gpu-rent)');
                    if (rentButton) {
                        // Traverse up to find the card container (div-based, not table)
                        let card = rentButton;
                        for (let i = 0; i < 8; i++) {
                            if (!card.parentElement) break;
                            card = card.parentElement;
                            const text = card.innerText;
                            // Found the card when it contains both h200 and price info
                            if (text.includes('h200') && text.includes('$') && 
                                (text.includes('Available') || text.includes('Min:'))) {
                                break;
                            }
                        }
                        
                        const text = card.innerText;
                        
                        // Extract all prices from the card
                        const allPrices = text.match(/\\$([0-9.]+)/g);
                        
                        // Extract min/max prices  
                        const minMatch = text.match(/Min:\\s*\\$([0-9.]+)/i);
                        const maxMatch = text.match(/Max:\\s*\\$([0-9.]+)/i);
                        
                        // The average price is typically the standalone price (last one)
                        let avgPrice = null;
                        if (allPrices && allPrices.length > 0) {
                            // Get last price as average
                            avgPrice = allPrices[allPrices.length - 1].replace('$', '');
                        }
                        
                        // Extract availability
                        const availMatch = text.match(/(\\d+)\\s*Available/i);
                        const totalMatch = text.match(/Total:\\s*(\\d+)/i);
                        
                        return {
                            avgPrice: avgPrice,
                            minPrice: minMatch ? minMatch[1] : null,
                            maxPrice: maxMatch ? maxMatch[1] : null,
                            available: availMatch ? availMatch[1] : null,
                            total: totalMatch ? totalMatch[1] : null,
                            allPrices: allPrices,
                            rowText: text.substring(0, 300)
                        };
                    }
                    
                    // Fallback: Find h200 text and traverse up to find prices
                    const allElements = Array.from(document.querySelectorAll('div, section, a'));
                    const h200El = allElements.find(el => 
                        el.innerText.trim().toLowerCase() === 'h200' && el.children.length === 0
                    );
                    
                    if (h200El) {
                        // Walk up to find container with prices
                        let container = h200El;
                        for (let i = 0; i < 8; i++) {
                            if (!container.parentElement) break;
                            container = container.parentElement;
                            if (container.innerText.includes('$')) break;
                        }
                        
                        const text = container.innerText;
                        const allPrices = text.match(/\\$([0-9.]+)/g);
                        
                        if (allPrices && allPrices.length > 0) {
                            return {
                                avgPrice: allPrices[allPrices.length - 1].replace('$', ''),
                                allPrices: allPrices,
                                source: 'h200-text-search'
                            };
                        }
                    }
                    
                    // Last fallback: search entire page
                    const bodyText = document.body.innerText;
                    const h200Section = bodyText.match(/h200[\\s\\S]{0,500}\\$([0-9.]+)/i);
                    if (h200Section) {
                        return { avgPrice: h200Section[1], source: 'body-text' };
                    }
                    
                    return null;
                """
                
                result = driver.execute_script(script)
                
                if result:
                    avg_price = None
                    min_price = None
                    max_price = None
                    
                    if result.get('avgPrice'):
                        avg_price = float(result['avgPrice'])
                    elif result.get('allPrices') and len(result['allPrices']) > 0:
                        # Get the last price as average
                        last_price = result['allPrices'][-1].replace('$', '')
                        avg_price = float(last_price)
                    
                    if result.get('minPrice'):
                        min_price = float(result['minPrice'])
                    if result.get('maxPrice'):
                        max_price = float(result['maxPrice'])
                    
                    if avg_price and 1.0 < avg_price < 10.0:
                        h200_prices["H200 SXM5 (Akash)"] = f"${avg_price:.2f}/hr"
                        h200_prices["_min_price"] = min_price
                        h200_prices["_max_price"] = max_price
                        h200_prices["_available"] = result.get('available')
                        h200_prices["_total"] = result.get('total')
                        
                        print(f"    ✓ Average: ${avg_price:.2f}/hr")
                        if min_price:
                            print(f"    ✓ Min: ${min_price:.2f}/hr")
                        if max_price:
                            print(f"    ✓ Max: ${max_price:.2f}/hr")
                        if result.get('available'):
                            print(f"    ✓ Available: {result['available']}/{result.get('total', '?')}")
                else:
                    print("    ⚠️  Could not find H200 pricing via JavaScript")
                    
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
    
    def save_to_json(self, prices: Dict[str, str], filename: str = "akash_h200_prices.json") -> bool:
        """Save results to a JSON file"""
        try:
            # Extract values
            avg_price = 0.0
            min_price = None
            max_price = None
            available = None
            total = None
            
            for key, value in prices.items():
                if key == "_min_price":
                    min_price = value
                elif key == "_max_price":
                    max_price = value
                elif key == "_available":
                    available = value
                elif key == "_total":
                    total = value
                elif not key.startswith("_"):
                    price_match = re.search(r'\$([0-9.]+)', str(value))
                    if price_match:
                        avg_price = float(price_match.group(1))
            
            output_data = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "provider": self.name,
                "providers": {
                    "Akash": {
                        "name": "Akash Network",
                        "url": self.base_url,
                        "variants": {
                            "H200 SXM5 (Akash)": {
                                "gpu_model": "H200",
                                "gpu_memory": "141GB",
                                "price_per_hour": round(avg_price, 2),
                                "currency": "USD",
                                "availability": "decentralized"
                            }
                        }
                    }
                },
                "notes": {
                    "instance_type": "Decentralized Cloud",
                    "gpu_model": "NVIDIA H200 SXM5",
                    "gpu_memory": "141Gi",
                    "gpu_count_per_instance": 1,
                    "pricing_type": "Variable (marketplace)",
                    "price_statistics": {
                        "average": round(avg_price, 2),
                        "minimum": round(min_price, 2) if min_price else None,
                        "maximum": round(max_price, 2) if max_price else None
                    },
                    "availability": {
                        "available": int(available) if available else None,
                        "total": int(total) if total else None
                    },
                    "source": "https://akash.network/pricing/gpus/"
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
    """Main function to run the Akash Network H200 scraper"""
    print("🚀 Akash Network H200 GPU Pricing Scraper")
    print("=" * 80)
    print("Note: Akash is a decentralized cloud with variable pricing")
    print("=" * 80)
    
    scraper = AkashH200Scraper()
    
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
