#!/usr/bin/env python3
"""
Run All H200 Scrapers
Executes all H200 GPU price scrapers and combines results into a single JSON file.

This script:
1. Runs each scraper in the h200 directory
2. Combines all individual JSON outputs into h200_combined_prices.json
3. Provides a summary of all extracted prices
"""

import subprocess
import sys
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import re


class H200ScraperRunner:
    """Runner for all H200 GPU scrapers"""
    
    def __init__(self, h200_dir: str = "."):
        self.h200_dir = Path(h200_dir)
        self.python_exe = sys.executable
        
    def find_all_scrapers(self) -> List[Path]:
        """Find all H200 scraper files"""
        scrapers = list(self.h200_dir.glob("*_h200_scraper.py"))
        return sorted(scrapers)
    
    def run_scraper(self, scraper_path: Path) -> bool:
        """Run a single scraper and return success status"""
        print(f"\n{'='*60}")
        print(f"🔄 Running: {scraper_path.name}")
        print('='*60)
        
        try:
            result = subprocess.run(
                [self.python_exe, str(scraper_path)],
                cwd=str(self.h200_dir),
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout per scraper
            )
            
            if result.returncode == 0:
                print(f"✅ {scraper_path.name} completed successfully")
                return True
            else:
                print(f"❌ {scraper_path.name} failed with return code {result.returncode}")
                if result.stderr:
                    print(f"   Error: {result.stderr[:200]}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {scraper_path.name} timed out after 120 seconds")
            return False
        except Exception as e:
            print(f"❌ Error running {scraper_path.name}: {str(e)[:100]}")
            return False
    
    def run_all_scrapers(self) -> Dict[str, bool]:
        """Run all scrapers and return results"""
        scrapers = self.find_all_scrapers()
        print(f"\n📋 Found {len(scrapers)} H200 scrapers\n")
        
        results = {}
        for scraper in scrapers:
            results[scraper.name] = self.run_scraper(scraper)
        
        return results
    
    def combine_prices(self) -> Dict:
        """Combine all H200 price JSON files into one"""
        json_files = list(self.h200_dir.glob("*_h200_prices.json"))
        
        combined = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_providers": 0,
            "providers": {},
            "price_summary": []
        }
        
        print(f"\n{'='*60}")
        print("📦 COMBINING ALL H200 PRICES")
        print('='*60)
        
        for json_file in sorted(json_files):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                provider_name = data.get("provider", json_file.stem.replace("_h200_prices", ""))
                
                # Extract price
                price = self._extract_price(data)
                
                if price and price > 0:
                    combined["providers"][provider_name] = {
                        "source_file": json_file.name,
                        "price_per_hour": round(price, 2),
                        "data": data
                    }
                    combined["price_summary"].append({
                        "provider": provider_name,
                        "price": round(price, 2)
                    })
                    combined["total_providers"] += 1
                    print(f"   ✓ {provider_name:25s} ${price:.2f}/hr")
                    
            except Exception as e:
                print(f"   ✗ Error loading {json_file.name}: {e}")
        
        # Sort price summary by price
        combined["price_summary"] = sorted(
            combined["price_summary"], 
            key=lambda x: x["price"]
        )
        
        return combined
    
    def _extract_price(self, data: Dict) -> float:
        """Extract price from provider data"""
        # Try nested providers structure
        if "providers" in data:
            for provider_name, provider_data in data["providers"].items():
                if "variants" in provider_data:
                    for variant_name, variant_data in provider_data["variants"].items():
                        if isinstance(variant_data, dict) and "price_per_hour" in variant_data:
                            return float(variant_data["price_per_hour"])
        
        # Try prices structure
        if "prices" in data:
            for variant, price_str in data["prices"].items():
                match = re.search(r'([0-9.]+)', str(price_str))
                if match:
                    return float(match.group(1))
        
        return 0.0
    
    def save_combined(self, combined: Dict, filename: str = "h200_combined_prices.json"):
        """Save combined prices to JSON"""
        output_path = self.h200_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(combined, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Combined prices saved to: {output_path}")
        return output_path


def main():
    """Main function to run all H200 scrapers"""
    print("🚀 H200 GPU Price Scraper Runner")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    runner = H200ScraperRunner()
    
    # Run all scrapers
    print("\n📋 PHASE 1: Running All Scrapers")
    print("=" * 60)
    results = runner.run_all_scrapers()
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 SCRAPER EXECUTION SUMMARY")
    print("=" * 60)
    
    successful = sum(1 for v in results.values() if v)
    failed = len(results) - successful
    
    for scraper, success in results.items():
        status = "✅" if success else "❌"
        print(f"   {status} {scraper}")
    
    print(f"\n   Total: {len(results)} scrapers")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    
    # Combine all prices
    print("\n📋 PHASE 2: Combining All Prices")
    combined = runner.combine_prices()
    
    # Save combined file
    runner.save_combined(combined)
    
    # Print final summary
    print("\n" + "=" * 60)
    print("🎯 FINAL PRICE SUMMARY (Sorted by Price)")
    print("=" * 60)
    
    for item in combined["price_summary"]:
        print(f"   {item['provider']:25s} ${item['price']:.2f}/hr")
    
    print(f"\n✅ Total providers with prices: {combined['total_providers']}")
    
    if combined["price_summary"]:
        min_price = combined["price_summary"][0]
        max_price = combined["price_summary"][-1]
        avg_price = sum(p["price"] for p in combined["price_summary"]) / len(combined["price_summary"])
        
        print(f"\n📊 Price Statistics:")
        print(f"   Lowest:  {min_price['provider']} at ${min_price['price']:.2f}/hr")
        print(f"   Highest: {max_price['provider']} at ${max_price['price']:.2f}/hr")
        print(f"   Average: ${avg_price:.2f}/hr")
    
    print(f"\n⏱️  Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
