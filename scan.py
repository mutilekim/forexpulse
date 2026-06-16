"""
ForexPulse Signal Scanner
Runs on a schedule via GitHub Actions. Fetches price data,
runs all strategies, and sends any signals to Telegram.
Author: Ruth Mutile Kimeu | BriefDesk Solutions
"""

import os
import asyncio
import logging
from datetime import datetime, timezone

import telegram

from strategy import SignalEngine
from data_fetcher import fetch_all_pairs

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Load from environment variables (set as GitHub Secrets)
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "")


async def scan_and_send():
    """Fetch data, analyze, and send signals."""
    if not BOT_TOKEN or not CHANNEL_ID:
        logger.error("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHANNEL_ID")
        return

    bot = telegram.Bot(token=BOT_TOKEN)
    engine = SignalEngine()

    logger.info("Fetching price data for all pairs...")
    try:
        all_data = fetch_all_pairs(period="1mo", interval="1h")
    except Exception as e:
        logger.error(f"Failed to fetch data: {e}")
        return

    if not all_data:
        logger.info("No data fetched. Markets may be closed.")
        return

    signals_sent = 0

    for pair, df in all_data.items():
        signals = engine.analyze(pair, df)

        for signal in signals:
            if signal.confidence == "LOW":
                continue

            message = (
                f"\U0001F4CA *ForexPulse Signal*\n"
                f"{'=' * 28}\n\n"
                f"{signal.to_message()}\n\n"
                f"\u23F0 {signal.timestamp.strftime('%Y-%m-%d %H:%M UTC')}"
            )

            try:
                await bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=message,
                    parse_mode="Markdown",
                )
                signals_sent += 1
                logger.info(f"Sent: {signal.direction.value} {signal.pair} ({signal.strategy})")
            except Exception as e:
                logger.error(f"Failed to send signal for {signal.pair}: {e}")

    if signals_sent == 0:
        logger.info("No signals found this scan. Markets may be consolidating.")
    else:
        logger.info(f"Scan complete. Sent {signals_sent} signal(s).")


def main():
    now = datetime.now(timezone.utc)
    logger.info(f"ForexPulse scan starting at {now.strftime('%Y-%m-%d %H:%M UTC')}")

    # Skip weekends (forex market closed)
    if now.weekday() >= 5:
        logger.info("Weekend. Forex market closed. Skipping scan.")
        return

    asyncio.run(scan_and_send())
    logger.info("Scan finished.")


if __name__ == "__main__":
    main()
