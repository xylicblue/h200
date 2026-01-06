#!/usr/bin/env python3
"""
H200 GPU Weighted Index Calculator

Calculates a weighted H200 GPU index price based on:
1. Hyperscalers (AWS, Azure, GCP, CoreWeave, Oracle) - 65% weight with 70-90% discounts
   - Discount blend: 80% at discounted rate + 20% at full price
   - Individual weights based on annual revenue
2. Neoclouds (all other providers) - 35% weight at full price
   - Individual weights based on annual revenue
3. Price normalization to base H200 config (141GB HBM3e, 3958 TFLOPS)

Revenue Sources (Approximate Annual):
- AWS: $100B cloud revenue
- Azure: $80B cloud revenue
- GCP: $40B cloud revenue
- Oracle: $20B cloud revenue
- CoreWeave: $2B AI cloud revenue

Neoclouds revenue estimated from public data and market presence.
"""

import json
import random
import re
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime


class H200IndexCalculator:
    """Calculate weighted H200 GPU index price based on revenue"""
    
    def __init__(self, h200_dir: str = "."):
        self.h200_dir = Path(h200_dir)
        
        # Base H200 configuration for normalization
        self.base_config = {
            "gpu_model": "H200",
            "gpu_memory_gb": 141,  # HBM3e
            "memory_bandwidth_tb_s": 4.8,
            "fp8_tflops": 3958,
            "form_factor": "SXM5"
        }
        
        # Define hyperscalers (5 major cloud providers)
        self.hyperscalers = ["AWS", "Azure", "Google Cloud", "CoreWeave", "Oracle"]
        
        # Hyperscaler discount range (70-90%)
        self.discount_min = 0.70
        self.discount_max = 0.90
        
        # Discount blend: 80% discounted, 20% full price
        self.discounted_weight = 0.80
        self.full_price_weight = 0.20
        
        # Total weight distribution
        self.hyperscaler_total_weight = 0.65  # 65%
        self.neocloud_total_weight = 0.35     # 35%
        
        # Hyperscaler individual weights based on annual revenue (must sum to 1.0)
        # Approximate annual cloud revenue:
        # - AWS: $100B → 41% of hyperscaler revenue
        # - Azure: $80B → 33% of hyperscaler revenue
        # - GCP: $40B → 17% of hyperscaler revenue
        # - Oracle: $20B → 8% of hyperscaler revenue
        # - CoreWeave: $2B → 1% of hyperscaler revenue (AI-focused)
        # Total: ~$242B
        self.hyperscaler_weights = {
            "AWS": 0.41,           # ~$100B annual
            "Azure": 0.33,         # ~$80B annual
            "Google Cloud": 0.17,  # ~$40B annual
            "Oracle": 0.08,        # ~$20B annual
            "CoreWeave": 0.01,     # ~$2B annual (AI-focused)
        }
        
        # Neocloud weights based on estimated annual revenue/market presence
        # These are estimates based on public funding, market presence, and GPU deployments
        # Total estimated: ~$1B combined
        self.neocloud_weights = {
            # Major neoclouds
            "Lambda Labs": 0.12,       # Well-funded, major AI cloud
            "Nebius": 0.10,            # Major presence
            "Crusoe": 0.08,            # $600M+ funding
            "Vultr": 0.07,             # Established VPS provider
            "RunPod": 0.06,            # Popular AI cloud
            "Vast.ai": 0.05,           # GPU marketplace
            "FluidStack": 0.05,        # GPU cloud
            "Hyperstack": 0.04,        # GPU cloud
            # Mid-tier neoclouds
            "Civo": 0.04,              # K8s-focused cloud
            "Shadeform": 0.04,         # GPU aggregator
            "Spheron": 0.03,           # Decentralized
            "Akash": 0.03,             # Decentralized cloud
            "Prime Intellect": 0.03,   # AI infrastructure
            "Valdi": 0.03,             # GPU marketplace
            "Verda": 0.025,            # GPU cloud
            "Fal.ai": 0.025,           # Serverless AI
            "GMI Cloud": 0.02,         # GPU cloud
            "JarvisLabs": 0.02,        # AI cloud
            "Hyperbolic": 0.02,        # GPU platform
            # Smaller neoclouds
            "IonStream": 0.015,        # H200 provider
            "AIME": 0.015,             # GPU cloud
            "AceCloud": 0.01,          # Indian GPU cloud
            "LeaderGPU": 0.01,         # European provider
            "ComputeThisHub": 0.01,    # GPU provider
            "Siam.ai": 0.01,           # Regional provider
            "Sesterce": 0.01,          # GPU cloud
            "Ori": 0.01,               # GPU cloud
            # Catch-all for unknown providers
            "default": 0.005,          # Default weight for unlisted
        }
    
    def load_prices_from_combined(self, combined_file: str = "h200_combined_prices.json") -> Dict[str, float]:
        """Load prices from combined JSON file"""
        file_path = self.h200_dir / combined_file
        
        if not file_path.exists():
            print(f"⚠️  {combined_file} not found. Loading from individual files...")
            return self.load_from_individual_files()
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        prices = {}
        for provider, provider_data in data.get("providers", {}).items():
            price = provider_data.get("price_per_hour", 0)
            if price > 0:
                prices[provider] = price
        
        return prices
    
    def load_from_individual_files(self) -> Dict[str, float]:
        """Load prices from individual JSON files"""
        prices = {}
        json_files = list(self.h200_dir.glob("*_h200_prices.json"))
        
        print(f"📂 Found {len(json_files)} H200 price files\n")
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    provider = data.get("provider", json_file.stem.replace("_h200_prices", ""))
                    price = self._extract_price_from_data(data)
                    
                    if price and price > 0:
                        prices[provider] = price
                        print(f"   ✓ {provider:25s} ${price:.2f}/hr")
            except Exception as e:
                print(f"   ✗ Error loading {json_file}: {e}")
        
        return prices
    
    def _extract_price_from_data(self, data: Dict) -> float:
        """Extract price value from provider data"""
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
    
    def normalize_price(self, price: float, provider_config: Dict = None) -> float:
        """
        Normalize price to base H200 configuration.
        
        If provider has different specs (e.g., 80GB vs 141GB memory),
        adjust price proportionally.
        """
        if not provider_config:
            return price
        
        # Memory normalization factor
        provider_memory = provider_config.get("gpu_memory_gb", 141)
        memory_factor = self.base_config["gpu_memory_gb"] / provider_memory
        
        # For now, we use a simple memory-based normalization
        # A 80GB H200 price would be scaled up by 141/80 = 1.76x
        normalized_price = price * memory_factor
        
        return normalized_price
    
    def categorize_providers(self, prices: Dict[str, float]) -> Tuple[Dict, Dict]:
        """Categorize providers into hyperscalers and neoclouds"""
        hyperscaler_prices = {}
        neocloud_prices = {}
        
        # Aliases for provider name matching
        hyperscaler_aliases = {
            "AWS": ["aws", "amazon"],
            "Azure": ["azure", "microsoft"],
            "Google Cloud": ["google", "gcp", "google_cloud", "google cloud"],
            "Oracle": ["oracle", "oci"],
            "CoreWeave": ["coreweave", "core_weave", "core weave"],
        }
        
        for provider, price in prices.items():
            provider_lower = provider.lower().strip()
            
            # Check if hyperscaler using aliases
            matched_hyperscaler = None
            for hs_name, aliases in hyperscaler_aliases.items():
                for alias in aliases:
                    if alias in provider_lower:
                        matched_hyperscaler = hs_name
                        break
                if matched_hyperscaler:
                    break
            
            if matched_hyperscaler:
                hyperscaler_prices[matched_hyperscaler] = price
            else:
                neocloud_prices[provider] = price
        
        return hyperscaler_prices, neocloud_prices
    
    def apply_hyperscaler_discounts(self, prices: Dict[str, float]) -> Dict[str, Dict]:
        """
        Apply random discounts (70-90%) to hyperscalers.
        
        Discount blend formula:
        effective_price = (discounted_price * 0.80) + (original_price * 0.20)
        
        where discounted_price = original_price * (1 - discount_rate)
        """
        discounted_data = {}
        
        print("\n" + "=" * 80)
        print("💰 HYPERSCALER DISCOUNT APPLICATION (70-90% discount range)")
        print("=" * 80)
        print("Blend: 80% at discounted rate + 20% at full price\n")
        
        for provider, original_price in prices.items():
            # Generate random discount between 70-90%
            discount_rate = random.uniform(self.discount_min, self.discount_max)
            
            # Calculate discounted price
            discounted_price = original_price * (1 - discount_rate)
            
            # Calculate blended effective price
            # effective = (discounted * 0.8) + (original * 0.2)
            effective_price = (discounted_price * self.discounted_weight) + \
                             (original_price * self.full_price_weight)
            
            discounted_data[provider] = {
                "original_price": original_price,
                "discount_rate": discount_rate,
                "discounted_price": discounted_price,
                "effective_price": effective_price
            }
            
            print(f"🏢 {provider}")
            print(f"   Original Price:     ${original_price:.2f}/hr")
            print(f"   Discount Applied:   {discount_rate*100:.1f}%")
            print(f"   Discounted Price:   ${discounted_price:.2f}/hr")
            print(f"   Blended Price:      ${effective_price:.2f}/hr")
            print(f"   (80% × ${discounted_price:.2f} + 20% × ${original_price:.2f})")
            print()
        
        return discounted_data
    
    def calculate_weighted_index(self, 
                                  hyperscaler_data: Dict[str, Dict],
                                  neocloud_prices: Dict[str, float]) -> Dict:
        """Calculate the final weighted index price"""
        
        print("=" * 80)
        print("⚖️  WEIGHTED INDEX CALCULATION")
        print("=" * 80)
        
        # =====================================================================
        # HYPERSCALER COMPONENT (65%)
        # =====================================================================
        print(f"\n📊 HYPERSCALERS (Total Weight: {self.hyperscaler_total_weight*100:.0f}%)")
        print("-" * 80)
        
        hyperscaler_weighted_sum = 0
        hyperscaler_details = []
        total_hyperscaler_weight_used = 0
        
        for provider, data in hyperscaler_data.items():
            if provider in self.hyperscaler_weights:
                individual_weight = self.hyperscaler_weights[provider]
                absolute_weight = individual_weight * self.hyperscaler_total_weight
                weighted_price = data["effective_price"] * absolute_weight
                
                hyperscaler_weighted_sum += weighted_price
                total_hyperscaler_weight_used += absolute_weight
                
                hyperscaler_details.append({
                    "provider": provider,
                    "original_price": data["original_price"],
                    "discount_rate": data["discount_rate"],
                    "effective_price": data["effective_price"],
                    "relative_weight": individual_weight,
                    "absolute_weight": absolute_weight,
                    "weighted_contribution": weighted_price
                })
                
                print(f"{provider:20s} ${data['effective_price']:6.2f}/hr × {absolute_weight*100:5.1f}% = ${weighted_price:.4f}")
        
        # Normalize if not all hyperscalers are present
        if total_hyperscaler_weight_used > 0 and total_hyperscaler_weight_used < self.hyperscaler_total_weight:
            normalization_factor = self.hyperscaler_total_weight / total_hyperscaler_weight_used
            hyperscaler_weighted_sum *= normalization_factor
            print(f"\n   ⚠️  Normalized (missing providers): factor = {normalization_factor:.2f}")
        
        print(f"{'':20s} {'':11s} {'':7s}   {'─'*20}")
        print(f"{'Hyperscaler Subtotal':20s} {'':11s} {'':7s}   ${hyperscaler_weighted_sum:.4f}")
        
        # =====================================================================
        # NEOCLOUD COMPONENT (35%)
        # =====================================================================
        print(f"\n📊 NEOCLOUDS (Total Weight: {self.neocloud_total_weight*100:.0f}%)")
        print("-" * 80)
        
        neocloud_weighted_sum = 0
        neocloud_details = []
        total_neocloud_weight_used = 0
        
        for provider, price in neocloud_prices.items():
            # Get weight from defined weights or use default
            individual_weight = self.neocloud_weights.get(provider, 
                               self.neocloud_weights.get("default", 0.005))
            absolute_weight = individual_weight * self.neocloud_total_weight
            weighted_price = price * absolute_weight
            
            neocloud_weighted_sum += weighted_price
            total_neocloud_weight_used += absolute_weight
            
            neocloud_details.append({
                "provider": provider,
                "price": price,
                "relative_weight": individual_weight,
                "absolute_weight": absolute_weight,
                "weighted_contribution": weighted_price
            })
            
            print(f"{provider:20s} ${price:6.2f}/hr × {absolute_weight*100:5.2f}% = ${weighted_price:.4f}")
        
        # Normalize if weights don't sum correctly
        if total_neocloud_weight_used > 0 and total_neocloud_weight_used < self.neocloud_total_weight:
            normalization_factor = self.neocloud_total_weight / total_neocloud_weight_used
            neocloud_weighted_sum *= normalization_factor
            print(f"\n   ⚠️  Normalized (weight adjustment): factor = {normalization_factor:.2f}")
        
        print(f"{'':20s} {'':11s} {'':7s}   {'─'*20}")
        print(f"{'Neocloud Subtotal':20s} {'':11s} {'':7s}   ${neocloud_weighted_sum:.4f}")
        
        # =====================================================================
        # FINAL INDEX
        # =====================================================================
        final_index = hyperscaler_weighted_sum + neocloud_weighted_sum
        
        print("\n" + "=" * 80)
        print("🎯 FINAL H200 INDEX PRICE")
        print("=" * 80)
        print(f"\nHyperscaler Component:    ${hyperscaler_weighted_sum:.4f} ({self.hyperscaler_total_weight*100:.0f}%)")
        print(f"Neocloud Component:       ${neocloud_weighted_sum:.4f} ({self.neocloud_total_weight*100:.0f}%)")
        print(f"{'─'*50}")
        print(f"H200 Weighted Index:      ${final_index:.2f}/hr")
        print("=" * 80)
        
        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "final_index_price": round(final_index, 2),
            "hyperscaler_component": round(hyperscaler_weighted_sum, 4),
            "neocloud_component": round(neocloud_weighted_sum, 4),
            "hyperscaler_count": len(hyperscaler_data),
            "neocloud_count": len(neocloud_prices),
            "hyperscaler_details": hyperscaler_details,
            "neocloud_details": neocloud_details,
            "weights": {
                "hyperscaler_total": self.hyperscaler_total_weight,
                "neocloud_total": self.neocloud_total_weight,
                "hyperscaler_individual": self.hyperscaler_weights,
                "discount_range": {"min": self.discount_min, "max": self.discount_max},
                "discount_blend": {
                    "discounted_weight": self.discounted_weight,
                    "full_price_weight": self.full_price_weight
                }
            },
            "base_config": self.base_config
        }
    
    def save_index_report(self, index_data: Dict, filename: str = "h200_weighted_index.json"):
        """Save index calculation report to JSON"""
        output_file = self.h200_dir / filename
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Index report saved to: {output_file}")
        return output_file


def main():
    """Main function to calculate H200 weighted index"""
    print("🚀 H200 GPU Weighted Index Calculator")
    print("=" * 80)
    print("Calculating weighted H200 index with:")
    print("  • Hyperscalers (65%): AWS, Azure, GCP, CoreWeave, Oracle")
    print("  • Neoclouds (35%): All other providers")
    print("  • Hyperscaler discounts: 70-90% (blend: 80% discounted + 20% full)")
    print("=" * 80)
    
    # Set random seed for reproducibility (optional)
    # random.seed(42)
    
    # Initialize calculator
    calculator = H200IndexCalculator()
    
    # Load all prices
    print("\n📂 Loading H200 Prices")
    print("-" * 80)
    prices = calculator.load_prices_from_combined()
    
    if not prices:
        print("\n❌ No H200 price data found!")
        return
    
    print(f"\n✓ Loaded {len(prices)} provider prices")
    
    # Categorize providers
    hyperscaler_prices, neocloud_prices = calculator.categorize_providers(prices)
    
    print(f"\n📊 Provider Categories:")
    print(f"   Hyperscalers found: {len(hyperscaler_prices)}")
    print(f"   Neoclouds found: {len(neocloud_prices)}")
    
    # Apply discounts to hyperscalers
    hyperscaler_data = calculator.apply_hyperscaler_discounts(hyperscaler_prices)
    
    # Calculate weighted index
    index_data = calculator.calculate_weighted_index(hyperscaler_data, neocloud_prices)
    
    # Save report
    calculator.save_index_report(index_data)
    
    print(f"\n✅ Index calculation complete!")
    print(f"\n🎯 Final H200 Weighted Index Price: ${index_data['final_index_price']:.2f}/hr")


if __name__ == "__main__":
    main()
