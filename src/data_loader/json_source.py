"""
JSON data source adapter for loading price history.
"""
import json
from pathlib import Path
from typing import Union
import pandas as pd


def load_json(source_path: Union[str, Path]) -> pd.DataFrame:
    """
    Load price history from JSON file.

    Expected JSON structure:
    {
        "qqq": [{"date": "YYYY-MM-DD", "adjClose": float}, ...],
        "qld": [{"date": "YYYY-MM-DD", "adjClose": float}, ...]
    }

    Args:
        source_path: Path to the JSON file

    Returns:
        DataFrame with Date index and QQQ, QLD columns
    """
    with open(source_path, 'r') as f:
        data = json.load(f)

    # Parse QQQ data
    qqq_df = pd.DataFrame(data['qqq'])
    qqq_df['date'] = pd.to_datetime(qqq_df['date'])
    qqq_df = qqq_df.rename(columns={'adjClose': 'QQQ'})
    qqq_df = qqq_df.set_index('date')[['QQQ']]

    # Parse QLD data
    qld_df = pd.DataFrame(data['qld'])
    qld_df['date'] = pd.to_datetime(qld_df['date'])
    qld_df = qld_df.rename(columns={'adjClose': 'QLD'})
    qld_df = qld_df.set_index('date')[['QLD']]

    # Inner join to ensure both have data on the same dates
    combined = qqq_df.join(qld_df, how='inner')

    # Sort by date ascending
    combined = combined.sort_index()

    return combined
