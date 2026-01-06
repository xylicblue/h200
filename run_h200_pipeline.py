#!/usr/bin/env python3
"""
H200 GPU Index Pipeline

This is the master script that runs the complete H200 index pipeline:
1. Combines existing price JSON files (does not run scrapers to avoid encoding issues)
2. Calculates the weighted H200 index
3. Pushes the result to Supabase

Usage:
    python run_h200_pipeline.py

For fresh data, run individual scrapers first, then run this pipeline.
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime


def run_step(step_name: str, script: str) -> bool:
    """Run a pipeline step"""
    print(f"\n{'='*60}")
    print(f"STEP: {step_name}")
    print('='*60)
    
    try:
        result = subprocess.run(
            [sys.executable, script],
            cwd=str(Path(__file__).parent),
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            print(f"\n[OK] {step_name} completed successfully")
            return True
        else:
            print(f"\n[FAIL] {step_name} failed with return code {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"\n[TIMEOUT] {step_name} timed out after 5 minutes")
        return False
    except FileNotFoundError:
        print(f"\n[ERROR] Script not found: {script}")
        return False
    except Exception as e:
        print(f"\n[ERROR] {step_name} error: {e}")
        return False


def main():
    """Run the complete H200 index pipeline"""
    print("=" * 60)
    print("H200 GPU INDEX PIPELINE")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # Step 1: Calculate weighted index (uses existing JSON files)
    results['Index Calculation'] = run_step(
        "Calculating H200 Weighted Index",
        "calculate_h200_index.py"
    )
    
    if not results['Index Calculation']:
        print("\n[ABORT] Pipeline aborted - index calculation failed")
        sys.exit(1)
    
    # Step 2: Push to Supabase
    results['Supabase Push'] = run_step(
        "Pushing to Supabase",
        "push_to_supabase.py"
    )
    
    # Summary
    print("\n" + "=" * 60)
    print("PIPELINE SUMMARY")
    print("=" * 60)
    
    all_success = True
    for step, success in results.items():
        status = "[OK]" if success else "[FAIL]"
        print(f"   {status} {step}")
        if not success:
            all_success = False
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if all_success:
        print("\n[SUCCESS] H200 Index Pipeline completed successfully!")
    else:
        print("\n[WARNING] Pipeline completed with errors")
        sys.exit(1)


if __name__ == "__main__":
    main()
