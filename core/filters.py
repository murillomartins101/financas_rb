"""
Filtros globais do app (período)
"""

import streamlit as st
import pandas as pd
from typing import Dict


class DataFilter:
    @staticmethod
    def apply_global_filters(data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        if not data:
            return {}

        start = st.session_state.get("filter_start_date")
        end = st.session_state.get("filter_end_date")

        # Todo período
        if start is None or end is None:
            return data

        filtered = {}
        for key, df in data.items():
            if df is None or df.empty:
                filtered[key] = df
                continue

            d = df.copy()

            if key == "shows" and "data_show" in d.columns:
                mask = (d["data_show"] >= start) & (d["data_show"] <= end)
                d = d[mask].copy()

            if key in ("transactions", "member_shares") and "data" in d.columns:
                mask = (d["data"] >= start) & (d["data"] <= end)
                d = d[mask].copy()

            filtered[key] = d

        return filtered


def display_current_filters():
    label = st.session_state.get("filter_period", "Todo período")
    start = st.session_state.get("filter_start_date")
    end = st.session_state.get("filter_end_date")

    if start and end:
        st.info(f"ℹ️ Filtros: **{label}** — {start.strftime('%d/%m/%Y')} até {end.strftime('%d/%m/%Y')}")
    else:
        st.info("ℹ️ Filtros: **Todo período**")
