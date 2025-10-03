"""Quickstart script to initialize the RADAR system"""
import sys
import subprocess
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.logging_config import log


def run_command(command: str, description: str):
    """Run a shell command and log the result"""
    log.info(f"Running: {description}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        log.info(f"✓ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        log.error(f"✗ {description} failed: {e.stderr}")
        return False


def main():
    """Run quickstart initialization"""
    log.info("=" * 60)
    log.info("RADAR Quickstart Initialization")
    log.info("=" * 60)
    
    steps = [
        ("python scripts/init_db.py", "Initialize databases"),
        ("python scripts/seed_sources.py", "Seed news sources"),
    ]
    
    for command, description in steps:
        if not run_command(command, description):
            log.error("Quickstart failed. Please check the errors above.")
            sys.exit(1)
    
    log.info("=" * 60)
    log.info("✓ Quickstart completed successfully!")
    log.info("=" * 60)
    log.info("")
    log.info("Next steps:")
    log.info("1. Start the API server: uvicorn src.api.main:app --reload")
    log.info("2. Start the worker: python -m src.workers.news_processor")
    log.info("3. Send sample news: python scripts/mock_parser.py")
    log.info("4. Test the API: curl -X POST http://localhost:8000/api/v1/analyze -H 'Content-Type: application/json' -d '{\"time_window_hours\": 24, \"top_k\": 5}'")


if __name__ == "__main__":
    main()

