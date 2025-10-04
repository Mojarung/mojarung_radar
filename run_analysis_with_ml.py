#!/usr/bin/env python3
"""
Script to run news analysis with ML model integration.
This demonstrates the complete pipeline with combined traditional and ML-based scoring.
"""

import sys
import os
import json
import argparse
from datetime import datetime

# Add app to path for Docker container
sys.path.append('/app')

from src.agents.graphs import run_analysis
from src.core.logging_config import log


def main():
    """Run news analysis with ML model integration"""
    parser = argparse.ArgumentParser(description="Run news analysis with ML model")
    parser.add_argument("--time-window", type=int, default=720,
                       help="Time window in hours (default: 24)")
    parser.add_argument("--top-k", type=int, default=5,
                       help="Number of top news to return (default: 5)")
    parser.add_argument("--output", type=str, default=None,
                       help="Output file for results (default: stdout)")
    parser.add_argument("--verbose", action="store_true",
                       help="Verbose output")
    parser.add_argument("--async-mode", action="store_true",
                       help="Use async LLM processing for faster execution")

    args = parser.parse_args()

    log.info("🚀 Starting news analysis with ML model integration")
    log.info(f"Time window: {args.time_window}h, Top K: {args.top_k}")

    try:
        # Run analysis
        results = run_analysis(
            time_window_hours=args.time_window,
            top_k=args.top_k,
            async_mode=args.async_mode
        )

        log.info(f"✅ Analysis completed! Found {len(results)} news items")

        # Prepare output
        output_data = {
            "timestamp": datetime.now().isoformat(),
            "config": {
                "time_window_hours": args.time_window,
                "top_k": args.top_k
            },
            "results_count": len(results),
            "results": results
        }

        # Output results
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            log.info(f"💾 Results saved to: {args.output}")
        else:
            # Pretty print to stdout
            print("\n" + "="*80)
            print("📰 TOP NEWS ANALYSIS RESULTS")
            print("="*80)

            for i, result in enumerate(results, 1):
                print(f"\n{i}. {result.get('headline', 'No title')}")
                print("-" * 60)

                if args.verbose:
                    print(f"Traditional Hotness: {result.get('hotness', 0):.3f}")
                    print(f"ML Hotness: {result.get('ml_hotness', 0):.3f}")
                    print(f"Combined Hotness: {result.get('combined_hotness', 0):.3f}")
                    print(f"Why Now: {result.get('why_now', 'N/A')}")

                    # Show entities if available
                    entities = result.get('entities', [])
                    if entities:
                        print(f"Entities: {', '.join(entities[:5])}")

                    # Show sources
                    sources = result.get('sources', [])
                    if sources:
                        print(f"Sources: {len(sources)} articles")

                # Show telegram post preview
                telegram_post = result.get('telegram_post', '')
                if telegram_post:
                    # Show first few lines
                    lines = telegram_post.split('\n')[:4]
                    print("Telegram Post:")
                    for line in lines:
                        print(f"  {line}")
                    if len(telegram_post.split('\n')) > 4:
                        print("  ...")

            print("\n" + "="*80)
            print("📊 SUMMARY")
            print("="*80)
            print(f"Total results: {len(results)}")
            print(f"Time window: {args.time_window} hours")
            print(f"Async mode: {args.async_mode}")
            print(f"Analysis completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            if args.async_mode:
                print("\n💡 Tip: Async mode processes multiple news clusters in parallel,")
                print("   significantly reducing total analysis time when processing many news items!")

        return 0

    except Exception as e:
        log.error(f"❌ Analysis failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
