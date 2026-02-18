"""
Camada de escrita (CRUD) para o app.
Encapsula operações no Google Sheets via core.google_sheets.
Retorna bool para a UI (pages/cadastros.py).
"""

import streamlit as st
from typing import Dict, Any
from core.google_sheets import write_row, update_row, delete_row


class DataWriter:
    def create_show(self, show_data: Dict[str, Any]) -> bool:
        res = write_row("shows", show_data)
        if not res.get("success"):
            st.error(f"Erro ao criar show: {res.get('error')}")
            return False
        st.success("Show criado com sucesso!")
        return True

    def update_show(self, show_id: str, show_data: Dict[str, Any]) -> bool:
        res = update_row("shows", show_id, id_column="show_id", updates=show_data)
        if not res.get("success"):
            st.error(f"Erro ao atualizar show: {res.get('error')}")
            return False
        st.success("Show atualizado com sucesso!")
        return True

    def delete_show(self, show_id: str) -> bool:
        res = delete_row("shows", show_id, id_column="show_id")
        if not res.get("success"):
            st.error(f"Erro ao excluir show: {res.get('error')}")
            return False
        st.success("Show excluído com sucesso!")
        return True

    def create_transaction(self, trans_data: Dict[str, Any]) -> bool:
        res = write_row("transactions", trans_data)
        if not res.get("success"):
            st.error(f"Erro ao criar transação: {res.get('error')}")
            return False
        st.success("Transação criada com sucesso!")
        return True

    def update_transaction(self, trans_id: str, trans_data: Dict[str, Any]) -> bool:
        res = update_row("transactions", trans_id, id_column="id", updates=trans_data)
        if not res.get("success"):
            st.error(f"Erro ao atualizar transação: {res.get('error')}")
            return False
        st.success("Transação atualizada com sucesso!")
        return True

    def delete_transaction(self, trans_id: str) -> bool:
        res = delete_row("transactions", trans_id, id_column="id")
        if not res.get("success"):
            st.error(f"Erro ao excluir transação: {res.get('error')}")
            return False
        st.success("Transação excluída com sucesso!")
        return True

    def create_payout_rule(self, rule_data: Dict[str, Any]) -> bool:
        res = write_row("payout_rules", rule_data)
        if not res.get("success"):
            st.error(f"Erro ao criar regra: {res.get('error')}")
            return False
        st.success("Regra criada com sucesso!")
        return True


data_writer = DataWriter()
