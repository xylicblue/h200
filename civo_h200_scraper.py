#!/usr/bin/env python3
"""
Civo H200 GPU Price Scraper
Extracts H200 pricing from Civo Cloud

Civo offers H200 GPUs in Small (1x) and Extra Large (8x) configurations.
Prices vary based on commitment period (on-demand to 36 months).

Reference: https://www.civo.com/ai/h200-gpu
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import time
from typing import Dict, Optional


class CivoH200Scraper:
    """Scraper for Civo Cloud H200 GPU pricing"""
    
    def __init__(self):
        self.name = "Civo"
        self.base_url = "https://www.civo.com/ai/h200-gpu"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
    
    def get_h200_prices(self) -> Dict[str, str]:
        """Main method to extract H200 prices from Civo"""
        print(f"🔍 Fetching {self.name} H200 pricing...")
        print("=" * 80)
        
        h200_prices = {}
        
        # Try multiple methods
        methods = [
            ("Civo Website Scraping", self._try_pricing_page),
            ("Selenium Scraper", self._try_selenium_scraper),
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
            print("\n❌ Failed to extract H200 pricing from Civo")
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
                    # Civo H200 pricing is around $2-5/hr for small instance
                    if 1.0 < price < 10.0:
                        return True
            except:
                continue
        return False
    
    def _try_pricing_page(self) -> Dict[str, str]:
        """Scrape Civo website for H200 pricing"""
        h200_prices = {}
        
        try:
            print(f"    Trying: {self.base_url}")
            response = requests.get(self.base_url, headers=self.headers, timeout=20)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                text_content = soup.get_text()
                
                print(f"      Content length: {len(text_content)}")
                
                # Check if page contains H200 data
                if 'H200' not in text_content:
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
        
        # Method 1: Look for sm-price class (commitment price for small plan)
        sm_price_elements = soup.find_all('span', class_='sm-price')
        for elem in sm_price_elements:
            price_text = elem.get_text().strip()
            price_match = re.search(r'\$([0-9.]+)', price_text)
            if price_match:
                price = float(price_match.group(1))
                if 1.0 < price < 10.0:
                    print(f"        ✓ Found sm-price: ${price:.2f}/hr")
                    prices["H200 Small 1x (Civo)"] = f"${price:.2f}/hr"
                    return prices
        
        # Method 2: Look in table structure
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                row_text = row.get_text()
                if 'Small' in row_text and 'H200' in row_text:
                    cells = row.find_all('td')
                    for cell in cells:
                        cell_text = cell.get_text()
                        # Look for the lower price (commitment price)
                        price_matches = re.findall(r'\$([0-9.]+)', cell_text)
                        for price_str in price_matches:
                            price = float(price_str)
                            if 1.0 < price < 10.0:
                                print(f"        ✓ Found in table: ${price:.2f}/hr")
                                prices["H200 Small 1x (Civo)"] = f"${price:.2f}/hr"
                                return prices
        
        # Method 3: Pattern matching in text
        patterns = [
            r'\$([0-9.]+)\s*Per\s*hour',
            r'\$([0-9.]+)\s*/\s*hr',
            r'Small.*?\$([0-9.]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            for price_str in matches:
                try:
                    price = float(price_str)
                    if 1.0 < price < 10.0:
                        print(f"        ✓ Found via pattern: ${price:.2f}/hr")
                        prices["H200 Small 1x (Civo)"] = f"${price:.2f}/hr"
                        return prices
                except ValueError:
                    continue
        
        return prices
    
    def _try_selenium_scraper(self) -> Dict[str, str]:
        """Use Selenium to scrape JavaScript-loaded pricing from Civo"""
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
                print(f"    Loading Civo page...")
                driver.get(self.base_url)
                
                print("    Waiting for dynamic content to load...")
                time.sleep(5)
                
                # Use JavaScript to extract H200 pricing
                script = """
                    // Look for sm-price class (commitment price for small plan)
                    const smPrice = document.querySelector('.sm-price');
                    if (smPrice) {
                        const text = smPrice.innerText;
                        const match = text.match(/\\$([0-9.]+)/);
                        if (match) {
                            return {
                                price: match[1],
                                source: 'sm-price'
                            };
                        }
                    }
                    
                    // Look in the pricing table
                    const table = document.querySelector('table');
                    if (table) {
                        const rows = table.querySelectorAll('tr');
                        for (const row of rows) {
                            const text = row.innerText;
                            if (text.includes('Small') && text.includes('H200')) {
                                // Find the lower price (commitment)
                                const prices = text.match(/\\$([0-9.]+)/g);
                                if (prices && prices.length > 0) {
                                    // Get the lowest price
                                    const numPrices = prices.map(p => parseFloat(p.replace('$', '')));
                                    const minPrice = Math.min(...numPrices.filter(p => p > 1 && p < 10));
                                    if (minPrice && isFinite(minPrice)) {
                                        return {
                                            price: minPrice.toString(),
                                            source: 'table-small-row'
                                        };
                                    }
                                }
                            }
                        }
                    }
                    
                    // Fallback: Find any price near "Per hour" text
                    const bodyText = document.body.innerText;
                    const match = bodyText.match(/\\$([0-9.]+)\\s*Per\\s*hour/i);
                    if (match) {
                        return {
                            price: match[1],
                            source: 'per-hour-text'
                        };
                    }
                    
                    return null;
                """
                
                result = driver.execute_script(script)
                
                if result and result.get('price'):
                    price = float(result['price'])
                    if 1.0 < price < 10.0:
                        h200_prices["H200 Small 1x (Civo)"] = f"${price:.2f}/hr"
                        print(f"    ✓ Found: ${price:.2f}/hr (source: {result.get('source', 'unknown')})")
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
    
    def save_to_json(self, prices: Dict[str, str], filename: str = "civo_h200_prices.json") -> bool:
        """Save results to a JSON file"""
        try:
            # Extract price
            price_value = 0.0
            for key, value in prices.items():
                if not key.startswith("_"):
                    price_match = re.search(r'\$([0-9.]+)', str(value))
                    if price_match:
                        price_value = float(price_match.group(1))
                        break
            
            output_data = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "provider": self.name,
                "providers": {
                    "Civo": {
                        "name": "Civo Cloud",
                        "url": self.base_url,
                        "variants": {
                            "H200 Small 1x (Civo)": {
                                "gpu_model": "H200",
                                "gpu_memory": "80GB",
                                "price_per_hour": round(price_value, 2),
                                "currency": "USD",
                                "availability": "on-demand"
                            }
                        }
                    }
                },
                "notes": {
                    "instance_type": "Small (1x GPU)",
                    "gpu_model": "NVIDIA H200",
                    "gpu_memory": "80GB",
                    "ram": "192 GB",
                    "vcpus": 48,
                    "storage": "400 GB NVMe",
                    "gpu_count_per_instance": 1,
                    "pricing_type": "Commitment (36 months)",
                    "on_demand_price": 3.49,
                    "commitment_prices": {
                        "6_months": 3.29,
                        "12_months": 3.19,
                        "24_months": 3.09,
                        "36_months": 2.99
                    },
                    "source": "https://www.civo.com/ai/h200-gpu"
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
    """Main function to run the Civo H200 scraper"""
    print("🚀 Civo Cloud H200 GPU Pricing Scraper")
    print("=" * 80)
    print("Note: Civo offers commitment-based pricing (best rate at 36 months)")
    print("=" * 80)
    
    scraper = CivoH200Scraper()
    
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
