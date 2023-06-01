# rp23-scraper

Downloads sessions for re:publica 2023 conference and outputs the data in a machine-readable form, either:

* CSV (`--csv`, the default),
* JSON (`--json`), plain dump containing the most data, or
* Frab Json (`--frab`), a JSON file in Frab format

Usage:

    ./scrape.py [--csv] [--frab] [--json]

You can pass multiple format arguments at once.
