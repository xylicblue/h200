#!/usr/bin/env python3
"""
AIME GPU Cloud H200 Price Scraper
Extracts H200 pricing from AIME

AIME offers NVIDIA H200 NVL 141GB virtual and bare metal servers.
Prices are in EUR and converted to USD using live exchange rates.

Reference: https://www.aime.info/en/gpucloud/#product-cloud-enterprise1
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import time
from typing import Dict, Optional


class AIMEH200Scraper:
    """Scraper for AIME GPU Cloud H200 pricing with EUR to USD conversion"""
    
    def __init__(self):
        self.name = "AIME"
        self.base_url = "https://www.aime.info/en/gpucloud/"
        # Exchange rate APIs (free, no API key required)
        self.exchange_apis = [
            "https://api.exchangerate-api.com/v4/latest/EUR",
            "https://open.er-api.com/v6/latest/EUR",
            "https://api.frankfurter.app/latest?from=EUR",
        ]
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
    
    def get_eur_to_usd_rate(self) -> Optional[float]:
        """Get live EUR to USD exchange rate from multiple APIs"""
        print("    💱 Fetching live EUR/USD exchange rate...")
        
        for api_url in self.exchange_apis:
            try:
                print(f"      Trying: {api_url}")
                response = requests.get(api_url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Handle different API response formats
                    if 'rates' in data:
                        rate = data['rates'].get('USD')
                        if rate:
                            print(f"      ✓ EUR/USD rate: {rate}")
                            return float(rate)
                            
            except Exception as e:
                print(f"      ⚠️ Error: {str(e)[:50]}")
                continue
        
        print("      ❌ Failed to get exchange rate from all APIs")
        return None
    
    def get_h200_prices(self) -> Dict[str, str]:
        """Main method to extract H200 prices from AIME"""
        print(f"🔍 Fetching {self.name} H200 pricing...")
        print("=" * 80)
        
        # First get the exchange rate
        eur_to_usd = self.get_eur_to_usd_rate()
        if not eur_to_usd:
            print("\n❌ Cannot proceed without exchange rate")
            return {}
        
        h200_prices = {}
        
        # Try multiple methods
        methods = [
            ("AIME Website Scraping", self._try_pricing_page),
            ("Selenium Scraper", self._try_selenium_scraper),
        ]
        
        for method_name, method_func in methods:
            print(f"\n📋 Method: {method_name}")
            try:
                prices = method_func()
                if prices and self._validate_prices(prices):
                    # Convert EUR to USD
                    for key, value in prices.items():
                        if not key.startswith('_'):
                            eur_price = float(re.search(r'€?([0-9.,]+)', value).group(1).replace(',', '.'))
                            usd_price = eur_price * eur_to_usd
                            h200_prices[key] = f"${usd_price:.2f}/hr"
                            h200_prices["_eur_price"] = eur_price
                            h200_prices["_exchange_rate"] = eur_to_usd
                            print(f"   ✅ Found H200: €{eur_price:.2f}/hr → ${usd_price:.2f}/hr")
                    break
                else:
                    print(f"   ❌ No valid prices found")
            except Exception as e:
                print(f"   ⚠️  Error: {str(e)[:100]}")
                continue
        
        if not h200_prices:
            print("\n❌ Failed to extract H200 pricing from AIME")
            return {}
        
        print(f"\n✅ Final extraction complete")
        return h200_prices
    
    def _validate_prices(self, prices: Dict[str, str]) -> bool:
        """Validate that prices are in a reasonable range (EUR)"""
        if not prices:
            return False
        
        for variant, price_str in prices.items():
            if 'Error' in variant or variant.startswith('_'):
                continue
            try:
                # Extract EUR price
                price_match = re.search(r'€?([0-9.,]+)', str(price_str))
                if price_match:
                    price = float(price_match.group(1).replace(',', '.'))
                    # AIME H200 pricing is around €3-10/hr
                    if 1.0 < price < 20.0:
                        return True
            except:
                continue
        return False
    
    def _try_pricing_page(self) -> Dict[str, str]:
        """Scrape AIME website for H200 pricing"""
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
        
        # Method 1: Look for "corresponds to X.XX € per hour" pattern
        patterns = [
            r'corresponds\s+to\s+([0-9.,]+)\s*€\s*per\s*hour',
            r'([0-9.,]+)\s*€\s*per\s*hour',
            r'([0-9.,]+)\s*€/h',
        ]
        
        # Find H200 section first
        h200_section = re.search(
            r'NVIDIA\s+H200\s+NVL\s+141GB[\s\S]*?corresponds\s+to\s+([0-9.,]+)\s*€\s*per\s*hour',
            text_content, re.IGNORECASE
        )
        
        if h200_section:
            price_str = h200_section.group(1).replace(',', '.')
            try:
                price = float(price_str)
                if 1.0 < price < 20.0:
                    print(f"        ✓ Found H200 price: €{price:.2f}/hr")
                    prices["H200 NVL 141GB (AIME)"] = f"€{price:.2f}/hr"
                    return prices
            except ValueError:
                pass
        
        # Method 2: Look in pricing cards (.u-pricing-v2)
        pricing_cards = soup.find_all(class_='u-pricing-v2')
        for card in pricing_cards:
            card_text = card.get_text()
            if 'H200' in card_text:
                for pattern in patterns:
                    match = re.search(pattern, card_text, re.IGNORECASE)
                    if match:
                        price_str = match.group(1).replace(',', '.')
                        try:
                            price = float(price_str)
                            if 1.0 < price < 20.0:
                                print(f"        ✓ Found H200 price in card: €{price:.2f}/hr")
                                prices["H200 NVL 141GB (AIME)"] = f"€{price:.2f}/hr"
                                return prices
                        except ValueError:
                            continue
        
        # Method 3: General pattern search
        for pattern in patterns:
            # Look for H200 followed by price within reasonable distance
            h200_match = re.search(
                rf'H200[\s\S]{{0,500}}{pattern}',
                text_content, re.IGNORECASE
            )
            if h200_match:
                price_str = h200_match.group(1).replace(',', '.')
                try:
                    price = float(price_str)
                    if 1.0 < price < 20.0:
                        print(f"        ✓ Found H200 price via pattern: €{price:.2f}/hr")
                        prices["H200 NVL 141GB (AIME)"] = f"€{price:.2f}/hr"
                        return prices
                except ValueError:
                    continue
        
        return prices
    
    def _try_selenium_scraper(self) -> Dict[str, str]:
        """Use Selenium to scrape JavaScript-loaded pricing from AIME"""
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
                print(f"    Loading AIME page...")
                driver.get(self.base_url)
                
                print("    Waiting for dynamic content to load...")
                time.sleep(5)
                
                # Use JavaScript to extract H200 pricing
                script = """
                    const allText = document.body.innerText;
                    
                    // Look for H200 section with hourly price
                    const h200Match = allText.match(/NVIDIA\\s+H200\\s+NVL\\s+141GB[\\s\\S]*?corresponds\\s+to\\s+([\\d,.]+)\\s*€\\s*per\\s*hour/i);
                    
                    if (h200Match) {
                        return {
                            price: h200Match[1].replace(',', '.'),
                            source: 'regex'
                        };
                    }
                    
                    // Try finding in pricing cards
                    const cards = document.querySelectorAll('.u-pricing-v2');
                    for (const card of cards) {
                        const text = card.innerText;
                        if (text.includes('H200')) {
                            const priceMatch = text.match(/corresponds\\s+to\\s+([\\d,.]+)\\s*€\\s*per\\s*hour/i);
                            if (priceMatch) {
                                return {
                                    price: priceMatch[1].replace(',', '.'),
                                    source: 'card'
                                };
                            }
                        }
                    }
                    
                    return null;
                """
                
                result = driver.execute_script(script)
                
                if result and result.get('price'):
                    price = float(result['price'])
                    if 1.0 < price < 20.0:
                        h200_prices["H200 NVL 141GB (AIME)"] = f"€{price:.2f}/hr"
                        print(f"    ✓ Found: €{price:.2f}/hr (source: {result.get('source', 'unknown')})")
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
    
    def save_to_json(self, prices: Dict[str, str], filename: str = "aime_h200_prices.json") -> bool:
        """Save results to a JSON file"""
        try:
            # Extract values
            usd_price = 0.0
            eur_price = 0.0
            exchange_rate = 0.0
            
            for key, value in prices.items():
                if key == "_eur_price":
                    eur_price = value
                elif key == "_exchange_rate":
                    exchange_rate = value
                elif not key.startswith("_"):
                    price_match = re.search(r'\$([0-9.]+)', str(value))
                    if price_match:
                        usd_price = float(price_match.group(1))
            
            output_data = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "provider": self.name,
                "providers": {
                    "AIME": {
                        "name": "AIME GPU Cloud",
                        "url": self.base_url,
                        "variants": {
                            "H200 NVL 141GB (AIME)": {
                                "gpu_model": "H200",
                                "gpu_memory": "141GB",
                                "price_per_hour": round(usd_price, 2),
                                "currency": "USD",
                                "availability": "on-demand"
                            }
                        }
                    }
                },
                "notes": {
                    "instance_type": "Virtual Server (1x GPU)",
                    "gpu_model": "NVIDIA H200 NVL",
                    "gpu_memory": "141GB",
                    "cpu": "30 vCores (Epyc Turin)",
                    "ram": "192 GB ECC",
                    "storage": "4 TB NVMe SSD",
                    "gpu_count_per_instance": 1,
                    "pricing_type": "Half-yearly plan (monthly rate)",
                    "original_currency": "EUR",
                    "original_price_eur": round(eur_price, 2),
                    "exchange_rate_eur_to_usd": round(exchange_rate, 4),
                    "source": "https://www.aime.info/en/gpucloud/"
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
    """Main function to run the AIME H200 scraper"""
    print("🚀 AIME GPU Cloud H200 Pricing Scraper")
    print("=" * 80)
    print("Note: AIME prices are in EUR, converting to USD")
    print("=" * 80)
    
    scraper = AIMEH200Scraper()
    
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
