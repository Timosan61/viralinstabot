#!/usr/bin/env python3
"""Quick run script for the bot."""

import asyncio
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.bot.main import main


if __name__ == "__main__":
    try:
        print("Starting Instagram Viral Bot...")
        print("Press Ctrl+C to stop")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)