# ForexPulse Signal Bot

Automated forex signal bot that scans 10 major currency pairs using RSI, EMA Crossover, MACD, and Bollinger Band strategies. Signals are delivered to a Telegram channel via GitHub Actions (free, no server needed).

**Built by Ruth Mutile Kimeu** | [BriefDesk Solutions](https://briefdeskke.co.ke)

## How It Works

Every hour during forex market hours (Monday to Friday), GitHub Actions runs the scanner automatically. It fetches price data, runs 4 technical analysis strategies across 10 pairs, and posts any signals to your Telegram channel with entry, stop loss, and take profit levels.

## Setup Guide

### 1. Create the Telegram bot and channel

- Message @BotFather on Telegram and send /newbot
- Save the bot token
- Create a public Telegram channel
- Add the bot as a channel administrator

### 2. Deploy to GitHub

- Create a new repository on GitHub (can be private)
- Push all these files to it
- Go to Settings > Secrets and variables > Actions
- Add two repository secrets:
  - TELEGRAM_BOT_TOKEN: your bot token from BotFather
  - TELEGRAM_CHANNEL_ID: your channel username (e.g. @forexpulse_signals)

### 3. Test it

- Go to the Actions tab in your repository
- Click "ForexPulse Signal Scanner"
- Click "Run workflow" to trigger a manual scan
- Check your Telegram channel for signals

The bot will then run automatically every hour on weekdays.

## Project Structure

```
forexpulse/
  scan.py               Main scanner (runs via GitHub Actions)
  strategy.py           Signal engine with 4 strategies
  data_fetcher.py       Price data from Yahoo Finance (free)
  requirements.txt      Python dependencies
  .github/
    workflows/
      scan.yml          GitHub Actions schedule
```

## Strategies

- RSI Reversal: oversold/overbought mean reversion
- EMA Crossover (9/21): momentum trend following
- MACD Crossover: trend confirmation signals
- Bollinger Bounce: volatility reversal setups

## Risk Disclaimer

ForexPulse is for educational and informational purposes only. Past performance does not guarantee future results. Forex trading involves substantial risk. Never risk more than you can afford to lose.

## License

MIT
