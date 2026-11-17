# Retail REITs: Who Is Winning, and Does It Show Up in the Stock?

ISA 401 Final Project, Fall 2026, Team [number], Section A

## Submission

| Item | Link |
|---|---|
| Dashboard (Tableau Public) | [link] |
| Recorded technical presentation (YouTube, unlisted) | [link] |
| This repository | https://github.com/tylerdraeger/ISA-Section-A-Final-Project |

## Team

| Member | What I built | Portfolio project entry |
|---|---|---|
| Tyler Draeger | [for example: the SEC API pulls and the LLM extraction] | [https://USERNAME.github.io/portfolio/#...] |
| Kenneth Kelly | [ ] | [ ] |

Each member adds this project to their own portfolio site, in their own words, with a link
back to this repository and the dashboard, and updates the Skills section of their portfolio
and of their `business_intelligence` README with skills they used in this project.

## The Question

Among publicly traded U.S. retail REITs, are shopping center owners doing better than malls
and net-lease REITs on the things that drive the business (occupancy, rent growth, earnings),
and does that show up in their stock returns and valuations, or do interest rates matter more?

Retail real estate went from "dead" (2020) to one of the tightest property types in the country.
Most coverage of that comes from company presentations or paid data services. We built our own
quarterly panel from public sources: the list of retail REITs from Nareit, financial statements
from the SEC, the operating numbers buried in each quarterly earnings press release (pulled out
with an LLM, since those are not in any free structured dataset), stock prices, and the 10-year
Treasury yield. No one source has all of these together.

## Data Sources

| Source | Link | Method | One row is | Code |
|---|---|---|---|---|
| Nareit REIT Directory (retail, listed, U.S.) | https://www.reit.com/investing/reit-directory | Web scraping (list pages + each REIT's profile page) | one REIT | `markdowns/01_acquire.Rmd` |
| SEC EDGAR XBRL `companyfacts` + ticker file | https://www.sec.gov/search-filings/edgar-application-programming-interfaces | API | one reported value for one period | `markdowns/01_acquire.Rmd` |
| Quarterly earnings press releases (8-K Item 2.02, Exhibit 99.1) | SEC EDGAR `submissions` API + filing archive | API to find and download, then **LLM structured extraction** (`ellmer`, `gpt-5.6-luna`) | one press release (one REIT, one quarter) | `markdowns/01_acquire.Rmd` |
| 10-year Treasury yield (`DGS10`) | https://fred.stlouisfed.org/series/DGS10 | API (FRED) | one trading day | `markdowns/01_acquire.Rmd` |
| Daily stock prices | Yahoo Finance chart API (`query1.finance.yahoo.com/v8/finance/chart`) | API | one ticker on one trading day | `markdowns/01_acquire.Rmd` |

## Pipeline

| Step | File | What it does |
|---|---|---|
| 1. Acquire | `markdowns/01_acquire.Rmd` | Scrapes the Nareit directory, matches tickers to SEC CIK numbers, pulls XBRL facts, finds and downloads every earnings press release since 2023, sends each one to the LLM for a fixed set of fields, and pulls FRED and Yahoo data. Every result is cached in `data/raw/`, so re-knitting does not re-scrape or re-pay for LLM calls. |
| 2. Clean and transform | `markdowns/02_clean.Rmd` | Splits and parses the scraped text, reshapes the profile fields long to wide, turns SEC `frame` codes into year/quarter, backs out Q4 (full year minus Q1-Q3), picks one revenue and one net income tag per REIT, assigns each press release to a quarter from its filing date, drops duplicate releases, gives each REIT one property type, and turns daily prices and yields into quarterly values. |
| 3. Merge | `markdowns/03_merge.Rmd` | Builds one row per REIT per finished quarter, left joins every source onto it, checks row counts after each join, and lists every row that did not match. |
| 4. Validate and summarize | `markdowns/04_validate.Rmd` | 13 validation rules (duplicates, failed joins, impossible values, LLM quarter vs. filing date, and whether each LLM number really appears in the press release text). Writes `validation_table.csv`, plus summary stats and exploratory charts. |

Raw files go in `data/raw/`; the cleaned and merged files go in `data/processed/`.

### How we handled data problems

- **Different tags for the same thing:** some REITs tag revenue as `Revenues`, others only as `OperatingLeaseLeaseIncome`. Same for net income. We pull all of them and use the first one that exists (`revenue_source` records which one).
- **SEC period labels are incomplete:** the SEC's `frame` label is blank on some facts, so we use each fact's start and end dates to decide which quarter it belongs to.
- **SEC data lag:** a few of the newest quarters (FRT, REG and UE for Q2-Q3 2026, KIM Q3 2026, NNN Q1 2026) are not in the SEC's `companyfacts` data yet. They stay `NA` and show up in the validation table.
- **No Q4 in the SEC data:** companies do not file a 10-Q for Q4, so Q4 = full year minus Q1-Q3. Flagged in `revenue_q4_derived`.
- **Duplicate records:** the SEC repeats the same number in later filings, and some REITs file more than one earnings 8-K in a quarter. We keep one per key (the latest).
- **Mismatched keys:** tickers are trimmed and checked against the SEC ticker file; quarters before a REIT started trading (Curbline, late 2024) are dropped instead of left as empty rows.
- **Missing values:** FRED's `"."` holiday values become `NA`. Net-lease REITs do not report same-property NOI or leasing spreads, so those stay `NA` on purpose.
- **Checking the LLM:** the quarter it reads is compared with the quarter from the filing date, and each number it returns is searched for in the original text. Anything that fails goes in the validation table.

## How to Reproduce

1. R version: 4.4 or newer. Packages: `rvest`, `httr2`, `jsonlite`, `dplyr`, `tidyr`, `purrr`, `stringr`, `readr`, `lubridate`, `ggplot2`, `ellmer`, `knitr` (the settings chunk of `01_acquire.Rmd` installs any that are missing).
2. API keys: create a `.Renviron` file in this folder with these names (values are your own), then restart R:
   - `SEC_USER_AGENT=Your Name your_email@miamioh.edu`
   - `FRED_API_KEY=`
   - `OPENAI_API_KEY=`
3. Knit the four files in `markdowns/` in order, 01 to 04. The first run of `01` takes a while (around 400 SEC requests and ~350 LLM calls). After that it reuses what is saved in `data/raw/`. Set `REFRESH = TRUE` at the top of `01` to pull everything fresh.

## The Final Dataset

- File: `data/processed/retail_reit_quarterly.csv`
- One row is: one retail REIT in one quarter (2023 Q1 to the last finished quarter)
- Rows and columns: 354 rows (24 REITs x up to 15 quarters, 2023 Q1 to 2026 Q3), 47 columns
- Companion file: `data/processed/retail_reit_profiles.csv` (one row per REIT, used for the map and the summary table)
- Validation table: `data/processed/validation_table.csv`
