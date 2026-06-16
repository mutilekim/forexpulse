"""
ForexPulse Signal Engine
Technical analysis strategies for forex signal generation.
Author: Ruth Mutile Kimeu | BriefDesk Solutions
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import datetime


class Direction(Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class Signal:
    pair: str
    direction: Direction
    entry_price: float
    stop_loss: float
    take_profit: float
    strategy: str
    confidence: str  # HIGH, MEDIUM, LOW
    risk_reward: float
    timestamp: datetime

    def to_message(self) -> str:
        arrow = "\U0001F7E2" if self.direction == Direction.BUY else "\U0001F534"
        pips_sl = abs(self.entry_price - self.stop_loss) * 10000
        pips_tp = abs(self.take_profit - self.entry_price) * 10000

        return (
            f"{arrow} *{self.direction.value} {self.pair}*\n"
            f"\n"
            f"Entry: `{self.entry_price:.5f}`\n"
            f"Stop Loss: `{self.stop_loss:.5f}` ({pips_sl:.1f} pips)\n"
            f"Take Profit: `{self.take_profit:.5f}` ({pips_tp:.1f} pips)\n"
            f"\n"
            f"Strategy: {self.strategy}\n"
            f"Confidence: {self.confidence}\n"
            f"Risk/Reward: 1:{self.risk_reward:.1f}\n"
            f"\n"
            f"_Manage your risk. Never risk more than 1-2% per trade._"
        )


def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def compute_ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def compute_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = compute_ema(series, fast)
    ema_slow = compute_ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = compute_ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def compute_bollinger(series: pd.Series, period: int = 20, std_dev: float = 2.0):
    sma = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    return upper, sma, lower


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return true_range.rolling(window=period).mean()


class SignalEngine:
    """Generates forex trading signals using multiple technical strategies."""

    def __init__(self, risk_pips: float = 30, reward_ratio: float = 2.0):
        self.risk_pips = risk_pips
        self.reward_ratio = reward_ratio

    def _pip_value(self, pair: str) -> float:
        """Returns pip value for position sizing."""
        if "JPY" in pair:
            return 0.01
        return 0.0001

    def analyze(self, pair: str, df: pd.DataFrame) -> list[Signal]:
        """Run all strategies on a pair and return any triggered signals."""
        if len(df) < 50:
            return []

        signals = []

        rsi_signal = self._rsi_strategy(pair, df)
        if rsi_signal:
            signals.append(rsi_signal)

        ema_signal = self._ema_crossover_strategy(pair, df)
        if ema_signal:
            signals.append(ema_signal)

        macd_signal = self._macd_strategy(pair, df)
        if macd_signal:
            signals.append(macd_signal)

        bb_signal = self._bollinger_strategy(pair, df)
        if bb_signal:
            signals.append(bb_signal)

        return signals

    def _calculate_sl_tp(self, pair: str, entry: float, direction: Direction, df: pd.DataFrame):
        """Calculate stop loss and take profit using ATR."""
        atr = compute_atr(df).iloc[-1]
        if pd.isna(atr):
            pip = self._pip_value(pair)
            atr = self.risk_pips * pip

        sl_distance = atr * 1.5
        tp_distance = sl_distance * self.reward_ratio

        if direction == Direction.BUY:
            sl = entry - sl_distance
            tp = entry + tp_distance
        else:
            sl = entry + sl_distance
            tp = entry - tp_distance

        return round(sl, 5), round(tp, 5)

    def _rsi_strategy(self, pair: str, df: pd.DataFrame) -> Optional[Signal]:
        """RSI oversold/overbought reversal strategy."""
        rsi = compute_rsi(df["close"])
        current_rsi = rsi.iloc[-1]
        prev_rsi = rsi.iloc[-2]

        if pd.isna(current_rsi) or pd.isna(prev_rsi):
            return None

        entry = df["close"].iloc[-1]
        direction = None
        confidence = "MEDIUM"

        # RSI crossing back above 30 (oversold reversal)
        if prev_rsi < 30 and current_rsi >= 30:
            direction = Direction.BUY
            if current_rsi < 35:
                confidence = "HIGH"

        # RSI crossing back below 70 (overbought reversal)
        elif prev_rsi > 70 and current_rsi <= 70:
            direction = Direction.SELL
            if current_rsi > 65:
                confidence = "HIGH"

        if direction is None:
            return None

        sl, tp = self._calculate_sl_tp(pair, entry, direction, df)
        rr = abs(tp - entry) / abs(entry - sl) if abs(entry - sl) > 0 else 0

        return Signal(
            pair=pair,
            direction=direction,
            entry_price=round(entry, 5),
            stop_loss=sl,
            take_profit=tp,
            strategy="RSI Reversal",
            confidence=confidence,
            risk_reward=round(rr, 1),
            timestamp=datetime.utcnow(),
        )

    def _ema_crossover_strategy(self, pair: str, df: pd.DataFrame) -> Optional[Signal]:
        """EMA 9/21 crossover strategy with trend filter."""
        ema_9 = compute_ema(df["close"], 9)
        ema_21 = compute_ema(df["close"], 21)
        ema_50 = compute_ema(df["close"], 50)

        curr_9, prev_9 = ema_9.iloc[-1], ema_9.iloc[-2]
        curr_21, prev_21 = ema_21.iloc[-1], ema_21.iloc[-2]
        curr_50 = ema_50.iloc[-1]

        entry = df["close"].iloc[-1]
        direction = None
        confidence = "MEDIUM"

        # Bullish crossover: EMA 9 crosses above EMA 21
        if prev_9 <= prev_21 and curr_9 > curr_21:
            direction = Direction.BUY
            # Higher confidence if price is above EMA 50 (with trend)
            if entry > curr_50:
                confidence = "HIGH"

        # Bearish crossover: EMA 9 crosses below EMA 21
        elif prev_9 >= prev_21 and curr_9 < curr_21:
            direction = Direction.SELL
            if entry < curr_50:
                confidence = "HIGH"

        if direction is None:
            return None

        sl, tp = self._calculate_sl_tp(pair, entry, direction, df)
        rr = abs(tp - entry) / abs(entry - sl) if abs(entry - sl) > 0 else 0

        return Signal(
            pair=pair,
            direction=direction,
            entry_price=round(entry, 5),
            stop_loss=sl,
            take_profit=tp,
            strategy="EMA Crossover (9/21)",
            confidence=confidence,
            risk_reward=round(rr, 1),
            timestamp=datetime.utcnow(),
        )

    def _macd_strategy(self, pair: str, df: pd.DataFrame) -> Optional[Signal]:
        """MACD crossover strategy."""
        macd_line, signal_line, histogram = compute_macd(df["close"])

        curr_macd, prev_macd = macd_line.iloc[-1], macd_line.iloc[-2]
        curr_signal, prev_signal = signal_line.iloc[-1], signal_line.iloc[-2]
        curr_hist = histogram.iloc[-1]

        if pd.isna(curr_macd) or pd.isna(prev_macd):
            return None

        entry = df["close"].iloc[-1]
        direction = None
        confidence = "MEDIUM"

        # Bullish: MACD crosses above signal
        if prev_macd <= prev_signal and curr_macd > curr_signal:
            direction = Direction.BUY
            if curr_hist > 0 and curr_macd < 0:
                confidence = "HIGH"

        # Bearish: MACD crosses below signal
        elif prev_macd >= prev_signal and curr_macd < curr_signal:
            direction = Direction.SELL
            if curr_hist < 0 and curr_macd > 0:
                confidence = "HIGH"

        if direction is None:
            return None

        sl, tp = self._calculate_sl_tp(pair, entry, direction, df)
        rr = abs(tp - entry) / abs(entry - sl) if abs(entry - sl) > 0 else 0

        return Signal(
            pair=pair,
            direction=direction,
            entry_price=round(entry, 5),
            stop_loss=sl,
            take_profit=tp,
            strategy="MACD Crossover",
            confidence=confidence,
            risk_reward=round(rr, 1),
            timestamp=datetime.utcnow(),
        )

    def _bollinger_strategy(self, pair: str, df: pd.DataFrame) -> Optional[Signal]:
        """Bollinger Band bounce strategy."""
        upper, middle, lower = compute_bollinger(df["close"])

        price = df["close"].iloc[-1]
        prev_price = df["close"].iloc[-2]

        if pd.isna(upper.iloc[-1]) or pd.isna(lower.iloc[-1]):
            return None

        direction = None
        confidence = "MEDIUM"

        # Price bouncing off lower band
        if prev_price <= lower.iloc[-2] and price > lower.iloc[-1]:
            direction = Direction.BUY
            rsi = compute_rsi(df["close"]).iloc[-1]
            if not pd.isna(rsi) and rsi < 40:
                confidence = "HIGH"

        # Price bouncing off upper band
        elif prev_price >= upper.iloc[-2] and price < upper.iloc[-1]:
            direction = Direction.SELL
            rsi = compute_rsi(df["close"]).iloc[-1]
            if not pd.isna(rsi) and rsi > 60:
                confidence = "HIGH"

        if direction is None:
            return None

        sl, tp = self._calculate_sl_tp(pair, price, direction, df)
        rr = abs(tp - price) / abs(price - sl) if abs(price - sl) > 0 else 0

        return Signal(
            pair=pair,
            direction=direction,
            entry_price=round(price, 5),
            stop_loss=sl,
            take_profit=tp,
            strategy="Bollinger Bounce",
            confidence=confidence,
            risk_reward=round(rr, 1),
            timestamp=datetime.utcnow(),
        )
