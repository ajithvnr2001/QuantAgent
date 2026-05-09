from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, Mapping
from urllib.error import URLError
from urllib.request import Request, urlopen


NSE_EQUITY_LIST_URL = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
INDIAN_EXCHANGE_SUFFIXES = (".NS", ".BO")

INDIAN_INDEX_SYMBOLS = {
    "NIFTY": "^NSEI",
    "NIFTY50": "^NSEI",
    "NIFTY_50": "^NSEI",
    "NIFTY 50": "^NSEI",
    "NIFTYBANK": "^NSEBANK",
    "BANKNIFTY": "^NSEBANK",
    "NIFTY BANK": "^NSEBANK",
    "SENSEX": "^BSESN",
    "BSESENSEX": "^BSESN",
    "INDIAVIX": "^INDIAVIX",
    "INDIA VIX": "^INDIAVIX",
}


class UniverseLoadError(RuntimeError):
    pass


def _clean_symbol(symbol: str) -> str:
    return str(symbol or "").strip().upper()


def _compact_symbol(symbol: str) -> str:
    return _clean_symbol(symbol).replace(" ", "").replace("_", "")


def normalize_nse_symbol(symbol: str) -> str:
    """Return an NSE-style symbol without a Yahoo exchange suffix."""
    clean = _clean_symbol(symbol)
    for suffix in INDIAN_EXCHANGE_SUFFIXES:
        if clean.endswith(suffix):
            return clean[: -len(suffix)]
    return clean


def to_yahoo_indian_symbol(symbol: str, default_exchange: str = "NS") -> str:
    """Convert plain Indian stock symbols to Yahoo Finance symbols.

    Examples:
    RELIANCE -> RELIANCE.NS
    TCS.NS -> TCS.NS
    500325.BO -> 500325.BO
    NIFTY50 -> ^NSEI
    """
    clean = _clean_symbol(symbol)
    if not clean:
        raise ValueError("empty symbol")

    mapped_index = INDIAN_INDEX_SYMBOLS.get(clean) or INDIAN_INDEX_SYMBOLS.get(
        _compact_symbol(clean)
    )
    if mapped_index:
        return mapped_index

    if clean.startswith("^") or "=" in clean:
        return clean

    if clean.endswith(INDIAN_EXCHANGE_SUFFIXES):
        return clean

    # A dot usually means the user already supplied a Yahoo exchange suffix
    # or another Yahoo-native symbol such as BRK.B.
    if "." in clean:
        return clean

    exchange = default_exchange.strip().upper().lstrip(".") or "NS"
    return f"{clean}.{exchange}"


def resolve_yahoo_symbol(
    symbol: str,
    explicit_mapping: Mapping[str, str] | None = None,
    default_exchange: str = "NS",
) -> str:
    """Resolve known aliases first, then default plain symbols to NSE Yahoo format."""
    clean = _clean_symbol(symbol)
    if not clean:
        raise ValueError("empty symbol")

    if explicit_mapping:
        if symbol in explicit_mapping:
            return explicit_mapping[symbol]
        if clean in explicit_mapping:
            return explicit_mapping[clean]

    return to_yahoo_indian_symbol(clean, default_exchange=default_exchange)


def unique_yahoo_symbols(
    symbols: Iterable[str], default_exchange: str = "NS"
) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for raw_symbol in symbols:
        symbol = to_yahoo_indian_symbol(raw_symbol, default_exchange=default_exchange)
        if symbol in seen:
            continue
        seen.add(symbol)
        output.append(symbol)
    return output


def parse_nse_equity_csv(
    content: str, allowed_series: tuple[str, ...] = ("EQ",)
) -> list[str]:
    reader = csv.DictReader(content.splitlines())
    symbols: list[str] = []

    for row in reader:
        normalized_row = {
            key.strip().upper(): value.strip()
            for key, value in row.items()
            if key
        }
        symbol = normalized_row.get("SYMBOL")
        series = normalized_row.get("SERIES", "")

        if not symbol:
            continue
        if allowed_series and series.upper() not in allowed_series:
            continue

        symbols.append(symbol)

    if not symbols:
        raise UniverseLoadError("NSE equity CSV did not contain any matching symbols")

    return unique_yahoo_symbols(symbols)


def load_all_nse_symbols(
    source_url: str = NSE_EQUITY_LIST_URL,
    timeout: int = 20,
    allowed_series: tuple[str, ...] = ("EQ",),
) -> list[str]:
    request = Request(
        source_url,
        headers={
            "User-Agent": "Mozilla/5.0 QuantAgent NSE loader",
            "Accept": "text/csv,*/*",
        },
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            content = response.read().decode("utf-8-sig")
    except (OSError, URLError) as exc:
        raise UniverseLoadError(
            f"Unable to load NSE symbol universe from {source_url}: {exc}"
        ) from exc

    return parse_nse_equity_csv(content, allowed_series=allowed_series)


def load_symbols_file(path: str | Path) -> list[str]:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    symbols: list[str] = []

    for line in lines:
        clean = line.split("#", 1)[0].strip()
        if not clean:
            continue
        symbols.extend(part for part in clean.replace(",", " ").split() if part)

    if not symbols:
        raise UniverseLoadError(f"No symbols found in {path}")

    return unique_yahoo_symbols(symbols)
