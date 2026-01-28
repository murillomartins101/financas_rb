from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict
import pandas as pd


# -----------------------
# Normalização / Validação
# -----------------------
VALID_SHOW_STATUS = {"PLANEJADO", "CONFIRMADO", "REALIZADO", "CANCELADO"}
VALID_TX_TIPO = {"ENTRADA", "SAIDA"}
VALID_PAY_STATUS = {"PAGO", "PENDENTE"}


def _to_date(df: pd.DataFrame, col: str) -> pd.DataFrame:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce").dt.date
    return df


def validate_shows(shows: pd.DataFrame) -> None:
    required = {"show_id", "data_show", "casa", "status"}
    missing = required - set(shows.columns)
    if missing:
        raise ValueError(f"shows: faltando colunas: {sorted(missing)}")

    bad = shows[~shows["status"].isin(VALID_SHOW_STATUS)]
    if len(bad) > 0:
        raise ValueError(f"shows: status inválido encontrado: {bad['status'].unique().tolist()}")

    if "publico" in shows.columns:
        bad_pub = shows.dropna(subset=["publico"])
        bad_pub = bad_pub[bad_pub["publico"].astype(float) < 0]
        if len(bad_pub) > 0:
            raise ValueError("shows: publico não pode ser negativo")


def validate_transactions(tx: pd.DataFrame) -> None:
    required = {"tx_id", "data", "tipo", "categoria", "descricao", "valor", "payment_status"}
    missing = required - set(tx.columns)
    if missing:
        raise ValueError(f"transactions: faltando colunas: {sorted(missing)}")

    bad_tipo = tx[~tx["tipo"].isin(VALID_TX_TIPO)]
    if len(bad_tipo) > 0:
        raise ValueError(f"transactions: tipo inválido: {bad_tipo['tipo'].unique().tolist()}")

    bad_pay = tx[~tx["payment_status"].isin(VALID_PAY_STATUS)]
    if len(bad_pay) > 0:
        raise ValueError(f"transactions: payment_status inválido: {bad_pay['payment_status'].unique().tolist()}")

    bad_val = tx[pd.to_numeric(tx["valor"], errors="coerce").isna()]
    if len(bad_val) > 0:
        raise ValueError("transactions: valor não numérico encontrado")

    if (pd.to_numeric(tx["valor"], errors="coerce") <= 0).any():
        raise ValueError("transactions: valor deve ser > 0 (use tipo para sinal)")


# -----------------------
# Cálculos principais
# -----------------------
def calc_cash_balance(tx: pd.DataFrame) -> float:
    paid = tx[tx["payment_status"] == "PAGO"].copy()
    paid["valor"] = pd.to_numeric(paid["valor"])
    entradas = paid.loc[paid["tipo"] == "ENTRADA", "valor"].sum()
    saidas = paid.loc[paid["tipo"] == "SAIDA", "valor"].sum()
    return float(entradas - saidas)


def calc_show_metrics(shows: pd.DataFrame, tx: pd.DataFrame) -> pd.DataFrame:
    """
    Retorna um DF por show com:
    - receita_reconhecida_show (0 se não REALIZADO)
    - despesa_show
    - resultado_liquido_show
    - publico (se existir)
    """
    s = shows.copy()
    t = tx.copy()

    _to_date(s, "data_show")
    _to_date(t, "data")

    validate_shows(s)
    validate_transactions(t)

    t = t[t["payment_status"] == "PAGO"].copy()
    t["valor"] = pd.to_numeric(t["valor"])
    t["show_id"] = t.get("show_id")

    # Agregações por show
    entradas = (
        t[(t["tipo"] == "ENTRADA") & (t["show_id"].notna())]
        .groupby("show_id")["valor"].sum()
        .rename("entradas_show_pago")
    )
    saidas = (
        t[(t["tipo"] == "SAIDA") & (t["show_id"].notna())]
        .groupby("show_id")["valor"].sum()
        .rename("saidas_show_pago")
    )

    out = s.merge(entradas, on="show_id", how="left").merge(saidas, on="show_id", how="left")
    out["entradas_show_pago"] = out["entradas_show_pago"].fillna(0.0)
    out["saidas_show_pago"] = out["saidas_show_pago"].fillna(0.0)

    # Receita reconhecida: só se REALIZADO
    out["receita_reconhecida_show"] = out.apply(
        lambda r: float(r["entradas_show_pago"]) if r["status"] == "REALIZADO" else 0.0,
        axis=1,
    )

    out["despesa_show"] = out["saidas_show_pago"].astype(float)
    out["resultado_liquido_show"] = out["receita_reconhecida_show"] - out["despesa_show"]

    cols = ["show_id", "data_show", "casa", "cidade", "status", "publico",
            "receita_reconhecida_show", "despesa_show", "resultado_liquido_show"]
    cols = [c for c in cols if c in out.columns]
    return out[cols].sort_values(["data_show", "casa"], ascending=[False, True]).reset_index(drop=True)


def calc_kpis(shows: pd.DataFrame, tx: pd.DataFrame) -> Dict[str, float]:
    m = calc_show_metrics(shows, tx)
    realizados = m[m["status"] == "REALIZADO"].copy()

    total_resultado = float(realizados["resultado_liquido_show"].sum())
    n_shows = int(len(realizados))
    media_por_show = float(total_resultado / n_shows) if n_shows else 0.0

    publico_total = float(realizados["publico"].fillna(0).sum()) if "publico" in realizados.columns else 0.0
    publico_medio = float(publico_total / n_shows) if n_shows else 0.0

    return {
        "caixa_atual": calc_cash_balance(tx),
        "resultado_liquido_total": total_resultado,
        "n_shows_realizados": float(n_shows),
        "valor_efetivo_medio_por_show": media_por_show,
        "publico_total": publico_total,
        "publico_medio": publico_medio,
    }
