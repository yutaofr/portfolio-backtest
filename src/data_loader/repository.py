"""
Data repository - unified data access interface.
Uses adapter pattern to support multiple data sources.
"""
import pandas as pd
from typing import Callable, Union
from pathlib import Path

# Type alias for data loader functions
DataLoaderFunc = Callable[[Union[str, Path]], pd.DataFrame]


def load_data(source_func: DataLoaderFunc, source_path: Union[str, Path]) -> pd.DataFrame:
    """
    High-order function to load data using injected loader.

    Args:
        source_func: Function that loads data from a source
        source_path: Path to the data source

    Returns:
        Cleaned and standardized DataFrame
    """
    df = source_func(source_path)
    return _standardize_data(df)


def _standardize_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize loaded data.

    - Ensure index is DatetimeIndex
    - Handle missing values (forward fill)
    - Ensure columns are numeric
    """
    # Ensure index is datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    # Forward fill any missing values
    df = df.ffill()

    # Ensure numeric columns
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Drop any rows with NaN after conversion
    df = df.dropna()

    return df
