"""data.py — load the tidy files built by prepare_data.py."""
import os
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
REAL = os.path.join(HERE, "data", "real")
def load_reviews(): return pd.read_csv(os.path.join(REAL, "reviews_clean.csv"))
def load_ca():      return pd.read_csv(os.path.join(REAL, "ca_panel.csv"))
def load_ofcom():   return pd.read_csv(os.path.join(REAL, "ofcom_complaints.csv"))
