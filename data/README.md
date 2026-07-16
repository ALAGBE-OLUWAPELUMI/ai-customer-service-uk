# Data

The analysis reads the tidy files in `real/`, rebuilt from `raw/` by
`python prepare_data.py`.

* `real/reviews_clean.csv` app store reviews for five UK telecom and energy brands,
  with a star rating and an AI-mention flag. Collected by the author.
* `real/ca_panel.csv` Citizens Advice energy supplier ratings, a supplier by quarter
  panel (public).
* `real/ofcom_complaints.csv` Ofcom Telecoms and Pay TV complaints per 100,000
  customers, by provider, service and quarter, 2010 to 2025 (public).

Raw source files live in `raw/` and are git ignored.
