import unittest

from indian_market import (
    parse_nse_equity_csv,
    resolve_yahoo_symbol,
    to_yahoo_indian_symbol,
    unique_yahoo_symbols,
)


class TestIndianMarketSymbols(unittest.TestCase):
    def test_plain_nse_symbol_gets_ns_suffix(self):
        self.assertEqual(to_yahoo_indian_symbol(" reliance "), "RELIANCE.NS")
        self.assertEqual(to_yahoo_indian_symbol("m&m"), "M&M.NS")
        self.assertEqual(to_yahoo_indian_symbol("MCDOWELL-N"), "MCDOWELL-N.NS")

    def test_existing_yahoo_suffixes_are_preserved(self):
        self.assertEqual(to_yahoo_indian_symbol("TCS.NS"), "TCS.NS")
        self.assertEqual(to_yahoo_indian_symbol("500325.BO"), "500325.BO")

    def test_indian_indices_map_to_yahoo_index_symbols(self):
        self.assertEqual(to_yahoo_indian_symbol("NIFTY50"), "^NSEI")
        self.assertEqual(to_yahoo_indian_symbol("Nifty Bank"), "^NSEBANK")
        self.assertEqual(to_yahoo_indian_symbol("SENSEX"), "^BSESN")

    def test_yahoo_native_symbols_are_preserved(self):
        self.assertEqual(to_yahoo_indian_symbol("^NSEI"), "^NSEI")
        self.assertEqual(to_yahoo_indian_symbol("NQ=F"), "NQ=F")

    def test_explicit_mapping_wins_before_indian_default(self):
        mapping = {"BTC": "BTC-USD", "AAPL": "AAPL"}
        self.assertEqual(resolve_yahoo_symbol("BTC", mapping), "BTC-USD")
        self.assertEqual(resolve_yahoo_symbol("AAPL", mapping), "AAPL")
        self.assertEqual(resolve_yahoo_symbol("HEG", mapping), "HEG.NS")

    def test_unique_yahoo_symbols_dedupes_after_normalization(self):
        self.assertEqual(
            unique_yahoo_symbols(["reliance", "RELIANCE.NS", "tcs"]),
            ["RELIANCE.NS", "TCS.NS"],
        )

    def test_parse_nse_equity_csv_only_keeps_eq_series(self):
        content = (
            "SYMBOL,NAME OF COMPANY,SERIES\n"
            "RELIANCE,Reliance Industries,EQ\n"
            "TCS,Tata Consultancy Services,EQ\n"
            "ABCBE,Some BE Share,BE\n"
            "M&M,Mahindra & Mahindra,EQ\n"
        )
        self.assertEqual(
            parse_nse_equity_csv(content),
            ["RELIANCE.NS", "TCS.NS", "M&M.NS"],
        )


if __name__ == "__main__":
    unittest.main()
