#!/usr/bin/env python3
"""
ComputeThisHub H200 GPU Price Scraper
Extracts H200 pricing from ComputeThisHub

ComputeThisHub offers dedicated bare metal H200 servers.

Reference: https://computethishub.com/
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import time
from typing import Dict, Optional


class ComputeThisHubH200Scraper:
    """Scraper for ComputeThisHub H200 GPU pricing"""
    
    def __init__(self):
        self.name = "ComputeThisHub"
        self.base_url = "https://computethishub.com/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
    
    def get_h200_prices(self) -> Dict[str, str]:
        """Main method to extract H200 prices from ComputeThisHub"""
        print(f"🔍 Fetching {self.name} H200 pricing...")
        print("=" * 80)
        
        h200_prices = {}
        
        # Try multiple methods
        methods = [
            ("ComputeThisHub Website Scraping", self._try_pricing_page),
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
            print("\n❌ Failed to extract H200 pricing from ComputeThisHub")
            return {}
        
        print(f"\n✅ Final extraction complete")
        return h200_prices
    
    def _validate_prices(self, prices: Dict[str, str]) -> bool:
        """Validate that prices are in a reasonable range"""
        if not prices:
            return False
        
        for variant, price_str in prices.items():
            if 'Error' in variant:
                continue
            try:
                price_match = re.search(r'\$?([0-9.]+)', str(price_str))
                if price_match:
                    price = float(price_match.group(1))
                    # ComputeThisHub H200 pricing is around $10-20/hr for multi-GPU
                    if 5.0 < price < 50.0:
                        return True
            except:
                continue
        return False
    
    def _try_pricing_page(self) -> Dict[str, str]:
        """Scrape ComputeThisHub website for H200 pricing"""
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
                
                # Extract from table
                prices = self._extract_from_table(soup)
                if prices:
                    h200_prices.update(prices)
                    
            else:
                print(f"      Status {response.status_code}")
                
        except Exception as e:
            print(f"      Error: {str(e)[:50]}...")
        
        return h200_prices
    
    def _extract_from_table(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract H200 prices from the pricing table"""
        prices = {}
        
        # Find all tables
        tables = soup.find_all('table')
        print(f"      Found {len(tables)} tables")
        
        for table in tables:
            table_text = table.get_text()
            
            # Only process tables with H200
            if 'H200' not in table_text:
                continue
            
            print(f"      📋 Processing table with H200 data")
            
            rows = table.find_all('tr')
            header_row = rows[0] if rows else None
            
            # Find price column index
            price_col_index = -1
            if header_row:
                headers = header_row.find_all(['th', 'td'])
                for i, header in enumerate(headers):
                    header_text = header.get_text().strip().lower()
                    if 'price' in header_text and ('hr' in header_text or 'hour' in header_text or '$/hr' in header_text):
                        price_col_index = i
                        print(f"        Found price column at index {i}")
                        break
            
            # Process data rows
            for row in rows[1:]:  # Skip header
                cells = row.find_all(['td', 'th'])
                row_text = ' '.join([cell.get_text().strip() for cell in cells])
                
                if 'H200' in row_text:
                    print(f"        H200 row: {row_text[:100]}")
                    
                    # Get GPU count (usually first column)
                    gpu_count = 1
                    if len(cells) > 0:
                        gpu_count_match = re.search(r'(\d+)', cells[0].get_text())
                        if gpu_count_match:
                            gpu_count = int(gpu_count_match.group(1))
                    
                    # Get price from identified column or last column
                    if price_col_index >= 0 and len(cells) > price_col_index:
                        price_text = cells[price_col_index].get_text().strip()
                    else:
                        # Try last column
                        price_text = cells[-1].get_text().strip()
                    
                    # Extract price value
                    price_match = re.search(r'(\d+(?:\.\d+)?)', price_text)
                    if price_match:
                        total_price = float(price_match.group(1))
                        # Calculate per-GPU price
                        per_gpu_price = total_price / gpu_count
                        
                        print(f"        ✓ {gpu_count}x H200: ${total_price}/hr → ${per_gpu_price:.2f}/GPU/hr")
                        prices[f"H200 {gpu_count}x (ComputeThisHub)"] = f"${per_gpu_price:.2f}/hr"
                        prices["_total_price"] = total_price
                        prices["_gpu_count"] = gpu_count
                        return prices
        
        return prices
    
    def _try_selenium_scraper(self) -> Dict[str, str]:
        """Use Selenium to scrape JavaScript-loaded pricing from ComputeThisHub"""
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
                print(f"    Loading ComputeThisHub page...")
                driver.get(self.base_url)
                
                print("    Waiting for dynamic content to load...")
                time.sleep(5)
                
                # Use JavaScript to extract H200 pricing from table
                script = """
                    const tables = Array.from(document.querySelectorAll('table'));
                    for (const table of tables) {
                        if (table.textContent.includes('Nvidia H200') || table.textContent.includes('H200')) {
                            const rows = Array.from(table.querySelectorAll('tr'));
                            const headerRow = rows[0];
                            const headers = Array.from(headerRow.querySelectorAll('th, td')).map(h => h.textContent.trim().toLowerCase());
                            
                            // Find price column
                            let priceColIndex = headers.findIndex(h => h.includes('price') && (h.includes('hr') || h.includes('hour')));
                            if (priceColIndex === -1) priceColIndex = headers.length - 1;
                            
                            // Find H200 row
                            const h200Row = rows.find(r => r.textContent.includes('H200'));
                            if (h200Row) {
                                const cells = Array.from(h200Row.querySelectorAll('td'));
                                const gpuCountMatch = cells[0].textContent.match(/(\\d+)/);
                                const gpuCount = gpuCountMatch ? parseInt(gpuCountMatch[1]) : 1;
                                
                                const priceText = cells[priceColIndex].textContent;
                                const priceMatch = priceText.match(/(\\d+(?:\\.\\d+)?)/);
                                
                                if (priceMatch) {
                                    const totalPrice = parseFloat(priceMatch[1]);
                                    const perGpuPrice = totalPrice / gpuCount;
                                    return {
                                        totalPrice: totalPrice,
                                        gpuCount: gpuCount,
                                        perGpuPrice: perGpuPrice
                                    };
                                }
                            }
                        }
                    }
                    return null;
                """
                
                result = driver.execute_script(script)
                
                if result:
                    total_price = result['totalPrice']
                    gpu_count = result['gpuCount']
                    per_gpu_price = result['perGpuPrice']
                    
                    h200_prices[f"H200 {gpu_count}x (ComputeThisHub)"] = f"${per_gpu_price:.2f}/hr"
                    h200_prices["_total_price"] = total_price
                    h200_prices["_gpu_count"] = gpu_count
                    print(f"    ✓ {gpu_count}x H200: ${total_price}/hr → ${per_gpu_price:.2f}/GPU/hr")
                else:
                    print("    ⚠️  Could not find H200 pricing via JavaScript")
                    
                    # Fallback to BeautifulSoup
                    page_source = driver.page_source
                    soup = BeautifulSoup(page_source, 'html.parser')
                    prices = self._extract_from_table(soup)
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
    
    def save_to_json(self, prices: Dict[str, str], filename: str = "computethishub_h200_prices.json") -> bool:
        """Save results to a JSON file"""
        try:
            # Extract values
            per_gpu_price = 0.0
            total_price = 0.0
            gpu_count = 4
            
            for key, value in prices.items():
                if key == "_total_price":
                    total_price = value
                elif key == "_gpu_count":
                    gpu_count = value
                elif not key.startswith("_"):
                    price_match = re.search(r'\$([0-9.]+)', str(value))
                    if price_match:
                        per_gpu_price = float(price_match.group(1))
            
            output_data = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "provider": self.name,
                "providers": {
                    "ComputeThisHub": {
                        "name": "ComputeThisHub",
                        "url": self.base_url,
                        "variants": {
                            f"H200 {gpu_count}x (ComputeThisHub)": {
                                "gpu_model": "H200",
                                "gpu_memory": "140GB",
                                "price_per_hour": round(per_gpu_price, 2),
                                "currency": "USD",
                                "availability": "dedicated"
                            }
                        }
                    }
                },
                "notes": {
                    "instance_type": "Dedicated Bare Metal",
                    "gpu_model": "NVIDIA H200",
                    "gpu_memory": "140GB",
                    "gpu_count_per_instance": gpu_count,
                    "total_instance_price": round(total_price, 2),
                    "pricing_type": "Dedicated",
                    "location": "Europe",
                    "source": "https://computethishub.com/"
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
    """Main function to run the ComputeThisHub H200 scraper"""
    print("🚀 ComputeThisHub H200 GPU Pricing Scraper")
    print("=" * 80)
    print("Note: ComputeThisHub offers dedicated bare metal H200 servers")
    print("=" * 80)
    
    scraper = ComputeThisHubH200Scraper()
    
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
