# AI Customer Service and Consumer Outcomes in UK Telecoms and Utilities

An empirical study of what moving customer service to AI does to consumer outcomes
in UK telecoms and utilities, using app store reviews, Ofcom complaints and the
Citizens Advice energy panel.

## Question
As firms route customer contact through AI, do consumers experience worse service,
and how does that sit against the wider trend in complaints?

## Data
* Around 2,000 app store reviews for Vodafone, O2, EE, British Gas and Octopus
  Energy, each with a star rating and an AI-mention flag (collected by the author).
* Ofcom complaints per 100,000 customers by provider and service, quarterly from
  2010 to 2025 (public).
* Citizens Advice energy supplier ratings, a supplier by quarter panel (public).

`prepare_data.py` cleans the raw sources into `data/real/`.

## What I find
* Reviews mentioning AI are rated 1.62 stars against 2.22 for other reviews, and the
  gap survives brand and year controls (0.62 stars lower, p below 0.001).
* Aggregate telecoms complaints fell over the period, fixed broadband from 35 to 7
  per 100,000, so this is not a story of collapsing service.
* In energy, higher rated suppliers get fewer complaints (r = -0.61), while call
  wait time alone does not predict complaints within suppliers.

The tension is the point: overall service improved, yet the AI channel itself draws
worse ratings. The write up is in `report/report.pdf`.

## Run it
```
pip install -r requirements.txt
python prepare_data.py   # cleans raw sources into data/real
python analyze.py        # figures, tables, metrics.json
python make_report.py    # builds report/report.pdf
```

## Caveats
Reviews are self selected and skew negative, the AI flag marks a mention rather than
confirmed AI use, and firm level AI adoption timing is unobserved, so these are
associations, not causal effects.

MIT licensed. Author: Oluwapelumi Alagbe.
