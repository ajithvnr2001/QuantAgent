# Indian Stocks + Vultr Inference Setup

This QuantAgent build supports Indian-stock analysis through Yahoo Finance and uses Vultr Inference as the default LLM provider.

## What Changed

- Plain NSE symbols are normalized to Yahoo Finance `.NS` symbols.
- BSE symbols with `.BO` are preserved.
- Common Indian indices map to Yahoo index symbols.
- The web UI includes Indian defaults such as `RELIANCE`, `TCS`, `INFY`, `HDFCBANK`, `ICICIBANK`, `SBIN`, `NIFTY50`, and `BANKNIFTY`.
- Vultr Inference is available as a first-class provider using the OpenAI-compatible endpoint.
- Vultr uses a text-first DeepSeek analysis path. This avoids the vision/tool-call graph that can stall or fail with text-only OpenAI-compatible models.

## LLM Configuration

The default provider is:

```text
Provider: Vultr Inference
Base URL: https://api.vultrinference.com/v1
Model: deepseek-ai/DeepSeek-V4-Pro
```

The local default config is in `default_config.py`. For operational use, prefer environment variables so credentials can be rotated without editing code:

```bash
export VULTR_API_KEY="your_vultr_inference_key_here"
export VULTR_BASE_URL="https://api.vultrinference.com/v1"
export VULTR_MODEL="deepseek-ai/DeepSeek-V4-Pro"
python web_interface.py
```

The web settings panel can also update the Vultr key at runtime.

## Supported Indian Symbol Formats

Use any of these in the custom symbol input or API payload:

```text
RELIANCE        -> RELIANCE.NS
TCS             -> TCS.NS
M&M             -> M&M.NS
MCDOWELL-N      -> MCDOWELL-N.NS
RELIANCE.NS     -> RELIANCE.NS
500325.BO       -> 500325.BO
NIFTY50         -> ^NSEI
BANKNIFTY       -> ^NSEBANK
SENSEX          -> ^BSESN
```

The conversion logic lives in `indian_market.py`. It follows the reference scanner pattern from `scans-test`: load NSE EQ-series symbols from the NSE equity CSV, then convert symbols to Yahoo Finance form.

## Running the Web App

```bash
pip install -r requirements.txt
python web_interface.py
```

Open:

```text
http://127.0.0.1:5000
```

Recommended workflow:

1. Choose an Indian asset button or enter a custom NSE/BSE symbol.
2. Use `1d`, `1w`, or `1mo` first for Indian equities.
3. Use the default market-session window unless you need a custom range. The form defaults to `09:00` through `16:30` and automatically chooses a wide history range for the selected timeframe.
4. Keep provider as `Vultr Inference`.
5. Run analysis.

## API Usage

Example Flask API request:

```bash
curl -X POST http://127.0.0.1:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "data_source": "live",
    "asset": "RELIANCE",
    "timeframe": "1d",
    "start_date": "2016-05-11",
    "start_time": "09:00",
    "end_date": "2026-05-08",
    "end_time": "16:30",
    "use_current_time": false,
    "redirect_to_output": false
  }'
```

Use `use_current_time: true` only when you intentionally want the app to replace the end date/time with the current timestamp. The UI defaults to the last completed `16:30` session to avoid future-time validation errors.

## NSE Universe Endpoint

The app includes an endpoint for loading the NSE EQ-series universe:

```bash
curl "http://127.0.0.1:5000/api/indian-symbols?limit=10"
```

The response contains Yahoo-formatted symbols:

```json
{
  "symbols": ["20MICRONS.NS", "21STCENMGM.NS"],
  "count": 10
}
```

Without `limit`, the endpoint returns the full loaded universe.

## Validation Commands

Compile the changed Python files:

```bash
python -m py_compile default_config.py indian_market.py llm_fallbacks.py trading_graph.py web_interface.py pattern_agent.py trend_agent.py
```

Run tests:

```bash
python -m unittest discover -s tests
```

Check live Yahoo Finance Indian data:

```bash
python - <<'PY'
from indian_market import resolve_yahoo_symbol
import yfinance as yf

for symbol in ["RELIANCE", "TCS", "M&M", "NIFTY50", "500325.BO"]:
    yahoo_symbol = resolve_yahoo_symbol(symbol, {"NIFTY50": "^NSEI"})
    frame = yf.download(yahoo_symbol, period="1mo", interval="1d", progress=False)
    print(symbol, "->", yahoo_symbol, "rows=", len(frame), "empty=", frame.empty)
PY
```

Check Vultr model connectivity:

```bash
python - <<'PY'
from openai import OpenAI
from default_config import DEFAULT_CONFIG

client = OpenAI(
    api_key=DEFAULT_CONFIG["vultr_api_key"],
    base_url=DEFAULT_CONFIG["vultr_base_url"],
)
response = client.chat.completions.create(
    model=DEFAULT_CONFIG["vultr_model"],
    messages=[{"role": "user", "content": "Reply with exactly: ok"}],
    max_tokens=8,
)
print(response.choices[0].message.content)
PY
```

Run a direct end-to-end analysis:

```bash
python -u - <<'PY'
from datetime import datetime, timedelta, UTC
from web_interface import analyzer

end = datetime.now(UTC).replace(tzinfo=None)
start = end - timedelta(days=120)
df = analyzer.fetch_yfinance_data_with_datetime("RELIANCE", "1d", start, end)
result = analyzer.run_analysis(df, "Reliance Industries (NSE)", "1d")
formatted = analyzer.extract_analysis_results(result)
print("success=", formatted.get("success"))
print("asset=", formatted.get("asset_name"))
print("candles=", formatted.get("data_length"))
print("decision=", formatted.get("final_decision", {}).get("decision"))
PY
```

## Operational Notes

- Yahoo Finance may return no data for invalid symbols, delisted stocks, holidays, or overly narrow date windows.
- Intraday Yahoo Finance intervals have shorter historical limits than daily/weekly/monthly intervals.
- Indian markets trade on exchange calendars; weekends and holidays reduce candle counts.
- The UI defaults to the widest practical range per timeframe: 7 days for `1m`, 60 days for `15m`, 730 days for hourly/4-hour, 3650 days for daily/weekly, and 7300 days for monthly.
- BSE equities need the `.BO` suffix. Plain symbols default to NSE `.NS`.
- `NIFTY50`, `BANKNIFTY`, and `SENSEX` are aliases for Yahoo index symbols.
- The Vultr path returns JSON fields compatible with the existing output page: technical indicators, pattern analysis, trend analysis, and final decision.
- Other providers still use the original LangGraph chart-image workflow.
