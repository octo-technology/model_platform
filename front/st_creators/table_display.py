import pandas as pd
import streamlit


def display_from_dataframe(input_df: pd.DataFrame):
    streamlit.dataframe(
        input_df,
        use_container_width=True,
    )
