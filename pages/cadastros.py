"""
Página de cadastro de registros (CRUD)
Implementa formulários para todas as entidades

FIXES IMPORTANTES:
- CRUD sempre usa base completa (sem filtros globais de período).
- Normaliza colunas (strip) e IDs (sempre string) para evitar "Nenhuma transação encontrada".
- Parse robusto de datas e valores vindos do Sheets (strings, vazios, etc.).
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
from typing import Optional

from core.data_loader import data_loader
from core.data_writer import data_writer
from core.validators import get_validation_message
from core.auth import check_permission
from core.constants import (
    TransactionType, PaymentStatus, ShowStatus, PayoutModel,
    OPERATIONAL_EXPENSE_CATEGORIES
)


# -----------------------------
# Helpers (robustos para Sheets)
# -----------------------------
def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def _find_first_existing_col(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    if df is None or df.empty:
        return None
    cols = set(df.columns)
    for c in candidates:
        if c in cols:
            return c
    return None


def _to_str_series(df: pd.DataFrame, col: str) -> pd.DataFrame:
    if df is None or df.empty or col not in df.columns:
        return df
    df = df.copy()
    df[col] = df[col].astype(str).str.strip()
    df.loc[df[col].isin(["", "None", "nan", "NaT"]), col] = ""
    return df


def _parse_date_to_date(value) -> datetime.date:
    """
    Aceita:
      - datetime/date
      - string '2026/01/20', '2026-01-20', '20/01/2026'
      - timestamp pandas
    Retorna date() sempre.
    """
    if value is None or value == "" or str(value).lower() in ("nan", "nat", "none"):
        return datetime.now().date()

    if hasattr(value, "date"):
        try:
            return value.date()
        except Exception:
            pass

    s = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(s[:10], fmt).date()
        except Exception:
            continue

    # fallback pandas
    try:
        dt = pd.to_datetime(s, errors="coerce")
        if pd.isna(dt):
            return datetime.now().date()
        return dt.date()
    except Exception:
        return datetime.now().date()


def _parse_float(value, default=0.0) -> float:
    if value is None or value == "" or str(value).lower() in ("nan", "none"):
        return float(default)
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()

    # remove moeda e espaços
    s = s.replace("R$", "").replace(" ", "")

    # casos comuns do BR:
    # "1.200,00" -> "1200.00"
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        # "1200,00" -> "1200.00"
        if "," in s:
            s = s.replace(",", ".")

    try:
        return float(s)
    except Exception:
        return float(default)


def main():
    """Página principal de cadastros"""
    st.title("Cadastro de Registros")

    if not check_permission("membro"):
        st.error("Você não tem permissão para acessar esta página.")
        return

    # CRUD deve carregar base completa (sem filtros globais)
    with st.spinner("Carregando dados..."):
        data = data_loader.load_all_data(force_refresh=False)

    tabs = st.tabs([
        "Shows",
        "Transacoes",
        "Regras de Rateio",
        "Membros",
        "Merchandising"
    ])

    with tabs[0]:
        render_shows_crud(data)

    with tabs[1]:
        render_transactions_crud(data)

    with tabs[2]:
        render_payout_rules_crud(data)

    with tabs[3]:
        render_members_crud(data)

    with tabs[4]:
        render_merchandising_crud(data)


# -----------------------------
# SHOWS
# -----------------------------
def render_shows_crud(data):
    """CRUD para shows"""
    st.subheader("Gerenciar Shows")

    action = st.radio(
        "Ação",
        ["Visualizar", "Adicionar", "Editar", "Excluir"],
        horizontal=True,
        key="shows_action"
    )

    shows_df = _normalize_columns(data.get('shows', pd.DataFrame()))

    # Normaliza ID e datas (evita None na tela)
    show_id_col = _find_first_existing_col(shows_df, ["show_id", "SHOW_ID", "id", "ID"])
    if show_id_col:
        shows_df = _to_str_series(shows_df, show_id_col)

    if "data_show" in shows_df.columns:
        shows_df["data_show"] = pd.to_datetime(shows_df["data_show"], errors="coerce")

    if "cache_acordado" in shows_df.columns:
        shows_df["cache_acordado"] = shows_df["cache_acordado"].apply(_parse_float)

    if action == "Visualizar":
        if not shows_df.empty:
            st.dataframe(shows_df, use_container_width=True, height=400)
            st.caption(f"Total: {len(shows_df)} shows")
        else:
            st.info("Nenhum show cadastrado")

    elif action == "Adicionar":
        render_create_show_form()

    elif action == "Editar":
        if shows_df.empty:
            st.info("Nenhum show para editar")
            return

        if not show_id_col:
            st.error(f"Coluna de ID do show não encontrada. Colunas: {shows_df.columns.tolist()}")
            return

        options = [x for x in shows_df[show_id_col].dropna().unique().tolist() if str(x).strip() != ""]
        options = sorted(options)

        show_id = st.selectbox("Selecione o show", options, key="edit_show_select")

        row_df = shows_df.loc[shows_df[show_id_col] == str(show_id)].copy()
        if row_df.empty:
            st.error("Show não encontrado (ID não bate com a base atual).")
            return

        show_data = row_df.iloc[0].to_dict()
        render_edit_show_form(show_data, show_id_col)

    elif action == "Excluir":
        if shows_df.empty:
            st.info("Nenhum show para excluir")
            return

        if not show_id_col:
            st.error(f"Coluna de ID do show não encontrada. Colunas: {shows_df.columns.tolist()}")
            return

        options = [x for x in shows_df[show_id_col].dropna().unique().tolist() if str(x).strip() != ""]
        options = sorted(options)

        show_id = st.selectbox("Selecione o show para excluir", options, key="delete_show_select")

        row_df = shows_df.loc[shows_df[show_id_col] == str(show_id)]
        if row_df.empty:
            st.error("Show não encontrado.")
            return

        show_row = row_df.iloc[0]
        st.warning(f"Show: {show_row.get('casa', '')} - {show_row.get('cidade', '')}")

        if st.button("Confirmar Exclusão", type="primary", key="confirm_delete_show"):
            if data_writer.delete_show(str(show_id)):
                st.success("Show excluído.")
                st.rerun()


def render_create_show_form():
    """Formulário para criar novo show"""
    st.markdown("### Novo Show")

    with st.form("create_show_form"):
        col1, col2 = st.columns(2)

        with col1:
            show_id = st.text_input(
                "ID do Show",
                value=f"S{datetime.now().strftime('%y%m%d')}{str(uuid.uuid4())[:2].upper()}"
            )
            data_show = st.date_input("Data do Show", value=datetime.now().date())
            casa = st.text_input("Casa/Local")
            cidade = st.text_input("Cidade")

        with col2:
            status = st.selectbox("Status", [s.value for s in ShowStatus])
            publico = st.number_input("Público", min_value=0, value=0)
            cache_acordado = st.number_input("Cachê Acordado (R$)", min_value=0.0, value=0.0)
            agente = st.text_input("Agente (opcional)")
            observacao = st.text_area("Observações")

        submitted = st.form_submit_button("Criar Show", type="primary")

        if submitted:
            show_data = {
                'show_id': str(show_id).strip(),
                'data_show': datetime.combine(data_show, datetime.min.time()),
                'casa': casa,
                'cidade': cidade,
                'status': status,
                'publico': int(publico),
                'cache_acordado': float(cache_acordado),
                'agente': agente,
                'observacao': observacao
            }

            validation_msg = get_validation_message('show', show_data)
            if isinstance(validation_msg, str) and validation_msg.startswith("OK:"):
                if data_writer.create_show(show_data):
                    st.success("Show criado!")
                    st.rerun()
            else:
                st.error(validation_msg if isinstance(validation_msg, str) else "Validação inválida.")


def render_edit_show_form(show_data, show_id_col="show_id"):
    """Formulário para editar show existente"""
    st.markdown("### Editar Show")

    with st.form("edit_show_form"):
        col1, col2 = st.columns(2)

        with col1:
            show_id = st.text_input("ID do Show", value=str(show_data.get(show_id_col, show_data.get("show_id", ""))), disabled=True)
            current_date = _parse_date_to_date(show_data.get('data_show'))
            data_show = st.date_input("Data do Show", value=current_date)
            casa = st.text_input("Casa/Local", value=show_data.get('casa', '') or '')
            cidade = st.text_input("Cidade", value=show_data.get('cidade', '') or '')

        with col2:
            status_options = [s.value for s in ShowStatus]
            current_status = show_data.get('status', 'CONFIRMADO') or 'CONFIRMADO'
            status_index = status_options.index(current_status) if current_status in status_options else 0
            status = st.selectbox("Status", status_options, index=status_index)

            publico = st.number_input("Público", min_value=0, value=int(show_data.get('publico', 0) or 0))
            cache_acordado = st.number_input("Cachê Acordado (R$)", min_value=0.0, value=_parse_float(show_data.get('cache_acordado', 0), 0.0))
            agente = st.text_input("Agente", value=show_data.get('agente', '') or '')
            observacao = st.text_area("Observações", value=show_data.get('observacao', '') or '')

        submitted = st.form_submit_button("Salvar Alterações", type="primary")

        if submitted:
            updated_data = {
                'show_id': str(show_id).strip(),
                'data_show': datetime.combine(data_show, datetime.min.time()),
                'casa': casa,
                'cidade': cidade,
                'status': status,
                'publico': int(publico),
                'cache_acordado': float(cache_acordado),
                'agente': agente,
                'observacao': observacao
            }

            validation_msg = get_validation_message('show', updated_data)
            if isinstance(validation_msg, str) and validation_msg.startswith("OK:"):
                if data_writer.update_show(str(show_id), updated_data):
                    st.success("Show atualizado!")
                    st.rerun()
            else:
                st.error(validation_msg if isinstance(validation_msg, str) else "Validação inválida.")


# -----------------------------
# TRANSAÇÕES
# -----------------------------
def render_transactions_crud(data):
    """CRUD para transações"""
    st.subheader("Gerenciar Transacoes")

    action = st.radio(
        "Ação",
        ["Visualizar", "Adicionar", "Editar", "Excluir"],
        horizontal=True,
        key="transactions_action"
    )

    transactions_df = _normalize_columns(data.get('transactions', pd.DataFrame()))

    # Descobrir coluna ID (resolve 'id' vs 'ID' etc.)
    id_col = _find_first_existing_col(transactions_df, ["id", "ID", "Id", "transaction_id", "transacao_id"])
    if not id_col and not transactions_df.empty:
        st.error(f"Coluna de ID da transação não encontrada. Colunas: {transactions_df.columns.tolist()}")
        return

    if id_col:
        transactions_df = _to_str_series(transactions_df, id_col)

    # Normalizar data/valor
    if "data" in transactions_df.columns:
        transactions_df["data"] = pd.to_datetime(transactions_df["data"], errors="coerce")
    if "valor" in transactions_df.columns:
        transactions_df["valor"] = transactions_df["valor"].apply(_parse_float)

    if action == "Visualizar":
        if transactions_df.empty:
            st.info("Nenhuma transação cadastrada")
            return

        col1, col2 = st.columns(2)
        with col1:
            tipo_filter = st.selectbox("Filtrar por tipo", ["Todos", "ENTRADA", "SAIDA"])
        with col2:
            status_filter = st.selectbox("Filtrar por status", ["Todos", "PAGO", "NÃO RECEBIDO", "ESTORNADO"])

        filtered_df = transactions_df.copy()
        if tipo_filter != "Todos" and "tipo" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['tipo'] == tipo_filter]
        if status_filter != "Todos" and "payment_status" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['payment_status'] == status_filter]

        st.dataframe(filtered_df, use_container_width=True, height=400)
        st.caption(f"Total: {len(filtered_df)} transações")

    elif action == "Adicionar":
        render_create_transaction_form(data)

    elif action == "Editar":
        if transactions_df.empty:
            st.info("Nenhuma transação para editar")
            return

        options = [x for x in transactions_df[id_col].dropna().unique().tolist() if str(x).strip() != ""]
        # Ordenação "int-aware" (165 vem antes de 1000)
        def _sort_key(x):
            xs = str(x)
            return (0, int(xs)) if xs.isdigit() else (1, xs)
        options = sorted(options, key=_sort_key)

        selected_id = st.selectbox("Selecione a transação", options, key="edit_trans_select")

        row_df = transactions_df.loc[transactions_df[id_col] == str(selected_id)].copy()
        if row_df.empty:
            st.error("Nenhuma transação encontrada! (ID não bate com a base atual — tipo/coluna/filtro)")
            return

        trans_data = row_df.iloc[0].to_dict()
        render_edit_transaction_form(trans_data, data, id_col=id_col)

    elif action == "Excluir":
        if transactions_df.empty:
            st.info("Nenhuma transação para excluir")
            return

        options = [x for x in transactions_df[id_col].dropna().unique().tolist() if str(x).strip() != ""]
        def _sort_key(x):
            xs = str(x)
            return (0, int(xs)) if xs.isdigit() else (1, xs)
        options = sorted(options, key=_sort_key)

        selected_id = st.selectbox("Selecione a transação para excluir", options, key="delete_trans_select")

        row_df = transactions_df.loc[transactions_df[id_col] == str(selected_id)]
        if row_df.empty:
            st.error("Transação não encontrada.")
            return

        row = row_df.iloc[0]
        st.warning(f"Transação: {row.get('descricao', '')} - R$ {float(row.get('valor', 0) or 0):,.2f}")

        if st.button("Confirmar Exclusão", type="primary", key="confirm_delete_trans"):
            if data_writer.delete_transaction(str(selected_id)):
                st.success("Transação excluída.")
                st.rerun()


def render_create_transaction_form(data):
    """Formulário para criar nova transação"""
    st.markdown("### Nova Transação")

    shows_df = _normalize_columns(data.get('shows', pd.DataFrame()))
    show_id_col = _find_first_existing_col(shows_df, ["show_id", "SHOW_ID", "id", "ID"])
    show_options = [""]

    if not shows_df.empty and show_id_col:
        shows_df = _to_str_series(shows_df, show_id_col)
        show_options += sorted([x for x in shows_df[show_id_col].unique().tolist() if str(x).strip() != ""])

    with st.form("create_transaction_form"):
        col1, col2 = st.columns(2)

        with col1:
            trans_id = st.text_input("ID da Transação", value=f"TRANS-{datetime.now().strftime('%Y%m%d%H%M%S')}")
            data_trans = st.date_input("Data", value=datetime.now().date())
            tipo = st.selectbox("Tipo", [t.value for t in TransactionType])

            all_categories = ["CACHÊS-MÚSICOS"] + OPERATIONAL_EXPENSE_CATEGORIES
            categoria = st.selectbox("Categoria", all_categories)
            subcategoria = st.text_input("Subcategoria (opcional)")

        with col2:
            descricao = st.text_input("Descrição")
            valor = st.number_input("Valor (R$)", min_value=0.01, value=100.0, step=10.0)
            payment_status = st.selectbox("Status de Pagamento", [s.value for s in PaymentStatus])
            show_id = st.selectbox("Show Relacionado (opcional)", show_options)
            conta = st.text_input("Conta (opcional)")

        submitted = st.form_submit_button("Criar Transação", type="primary")

        if submitted:
            trans_data = {
                'id': str(trans_id).strip(),
                'data': datetime.combine(data_trans, datetime.min.time()),
                'tipo': tipo,
                'categoria': categoria,
                'subcategoria': subcategoria,
                'descricao': descricao,
                'valor': float(valor),
                'payment_status': payment_status,
                'show_id': str(show_id).strip() if show_id else None,
                'conta': conta
            }

            validation_msg = get_validation_message('transaction', trans_data)
            if isinstance(validation_msg, str) and validation_msg.startswith("OK:"):
                ok = data_writer.create_transaction(trans_data)
                if ok:
                    st.success("Transação criada!")
                    st.rerun()
                else:
                    st.error("Erro ao criar transação (data_writer retornou False).")
            else:
                st.error(validation_msg if isinstance(validation_msg, str) else "Validação inválida.")


def render_edit_transaction_form(trans_data, data, id_col="id"):
    """Formulário para editar transação existente"""
    st.markdown("### Editar Transação")

    shows_df = _normalize_columns(data.get('shows', pd.DataFrame()))
    show_id_col = _find_first_existing_col(shows_df, ["show_id", "SHOW_ID", "id", "ID"])
    show_options = [""]

    if not shows_df.empty and show_id_col:
        shows_df = _to_str_series(shows_df, show_id_col)
        show_options += sorted([x for x in shows_df[show_id_col].unique().tolist() if str(x).strip() != ""])

    with st.form("edit_transaction_form"):
        col1, col2 = st.columns(2)

        with col1:
            trans_id = st.text_input("ID", value=str(trans_data.get(id_col, trans_data.get("id", ""))), disabled=True)
            current_date = _parse_date_to_date(trans_data.get('data'))
            data_trans = st.date_input("Data", value=current_date)

            tipo_options = [t.value for t in TransactionType]
            current_tipo = trans_data.get('tipo', 'ENTRADA') or 'ENTRADA'
            tipo_index = tipo_options.index(current_tipo) if current_tipo in tipo_options else 0
            tipo = st.selectbox("Tipo", tipo_options, index=tipo_index)

            all_categories = ["CACHÊS-MÚSICOS"] + OPERATIONAL_EXPENSE_CATEGORIES
            current_cat = trans_data.get('categoria', '') or ''
            cat_index = all_categories.index(current_cat) if current_cat in all_categories else 0
            categoria = st.selectbox("Categoria", all_categories, index=cat_index)

            subcategoria = st.text_input("Subcategoria", value=trans_data.get('subcategoria', '') or '')

        with col2:
            descricao = st.text_input("Descrição", value=trans_data.get('descricao', '') or '')
            valor = st.number_input("Valor (R$)", min_value=0.01, value=_parse_float(trans_data.get('valor', 100), 100.0), step=10.0)

            status_options = [s.value for s in PaymentStatus]
            current_status = trans_data.get('payment_status', 'PAGO') or 'PAGO'
            status_index = status_options.index(current_status) if current_status in status_options else 0
            payment_status = st.selectbox("Status de Pagamento", status_options, index=status_index)

            current_show = str(trans_data.get('show_id', '') or '').strip()
            show_index = show_options.index(current_show) if current_show in show_options else 0
            show_id = st.selectbox("Show Relacionado", show_options, index=show_index)

            conta = st.text_input("Conta", value=trans_data.get('conta', '') or '')

        submitted = st.form_submit_button("Salvar Alterações", type="primary")

        if submitted:
            updated_data = {
                'id': str(trans_id).strip(),
                'data': datetime.combine(data_trans, datetime.min.time()),
                'tipo': tipo,
                'categoria': categoria,
                'subcategoria': subcategoria,
                'descricao': descricao,
                'valor': float(valor),
                'payment_status': payment_status,
                'show_id': str(show_id).strip() if show_id else None,
                'conta': conta
            }

            validation_msg = get_validation_message('transaction', updated_data)
            if isinstance(validation_msg, str) and validation_msg.startswith("OK:"):
                ok = data_writer.update_transaction(str(trans_id), updated_data, key_column=id_col)
                if ok:
                    st.success("Transação atualizada!")
                    st.rerun()
                else:
                    st.error("Nenhuma transação encontrada! (ID/coluna não bate no Sheets)")
            else:
                st.error(validation_msg if isinstance(validation_msg, str) else "Validação inválida.")


# -----------------------------
# RATEIO / MEMBROS / MERCH
# (mantidos como estavam, com pequenas robustezes)
# -----------------------------
def render_payout_rules_crud(data):
    """CRUD para regras de rateio"""
    st.subheader("Gerenciar Regras de Rateio")

    action = st.radio(
        "Ação",
        ["Visualizar", "Adicionar"],
        horizontal=True,
        key="payout_action"
    )

    rules_df = _normalize_columns(data.get('payout_rules', pd.DataFrame()))

    if action == "Visualizar":
        if not rules_df.empty:
            st.dataframe(rules_df, use_container_width=True, height=300)
            st.caption(f"Total: {len(rules_df)} regras")
        else:
            st.info("Nenhuma regra de rateio cadastrada")

    elif action == "Adicionar":
        render_create_payout_rule_form()


def render_create_payout_rule_form():
    """Formulário para criar nova regra de rateio"""
    st.markdown("### Nova Regra de Rateio")

    with st.form("create_payout_rule_form"):
        col1, col2 = st.columns(2)

        with col1:
            rule_id = st.text_input(
                "ID da Regra",
                value=f"RULE-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
            )
            nome_regra = st.text_input("Nome da Regra")
            modelo = st.selectbox("Modelo", [m.value for m in PayoutModel])
            ativa = st.selectbox("Ativa", ["SIM", "NÃO"])

        with col2:
            pct_caixa = st.slider("% para Caixa", 0, 100, 30)
            pct_musicos = st.slider("% para Músicos", 0, 100, 70)
            vigencia_inicio = st.date_input("Início da Vigência", value=datetime.now().date())
            vigencia_fim = st.date_input("Fim da Vigência (opcional)", value=None)

        if pct_caixa + pct_musicos != 100:
            st.warning(f"Atenção: A soma dos percentuais é {pct_caixa + pct_musicos}% (deveria ser 100%)")

        submitted = st.form_submit_button("Criar Regra", type="primary")

        if submitted:
            rule_data = {
                'rule_id': str(rule_id).strip(),
                'nome_regra': nome_regra,
                'modelo': modelo,
                'pct_caixa': int(pct_caixa),
                'pct_musicos': int(pct_musicos),
                'ativa': ativa,
                'vigencia_inicio': datetime.combine(vigencia_inicio, datetime.min.time()),
                'vigencia_fim': datetime.combine(vigencia_fim, datetime.min.time()) if vigencia_fim else None
            }

            validation_msg = get_validation_message('payout_rule', rule_data)
            if isinstance(validation_msg, str) and validation_msg.startswith("OK:"):
                if data_writer.create_payout_rule(rule_data):
                    st.success("Regra criada!")
                    st.rerun()
            else:
                st.error(validation_msg if isinstance(validation_msg, str) else "Validação inválida.")


def render_members_crud(data):
    """CRUD para membros"""
    st.subheader("Gerenciar Membros")

    action = st.radio(
        "Ação",
        ["Visualizar", "Adicionar"],
        horizontal=True,
        key="members_action"
    )

    members_df = _normalize_columns(data.get('members', pd.DataFrame()))

    if action == "Visualizar":
        if not members_df.empty:
            st.dataframe(members_df, use_container_width=True, height=300)
            st.caption(f"Total: {len(members_df)} membros")
        else:
            st.info("Nenhum membro cadastrado")

    elif action == "Adicionar":
        render_create_member_form()


def render_create_member_form():
    """Formulário para criar novo membro"""
    st.markdown("### Novo Membro")

    with st.form("create_member_form"):
        col1, col2 = st.columns(2)

        with col1:
            member_id = st.text_input("ID do Membro", value=f"MEM-{str(uuid.uuid4())[:8].upper()}")
            nome = st.text_input("Nome Completo")
            instrumento = st.text_input("Instrumento/Função")

        with col2:
            email = st.text_input("Email (opcional)")
            telefone = st.text_input("Telefone (opcional)")
            ativo = st.selectbox("Status", ["ATIVO", "INATIVO"])

        submitted = st.form_submit_button("Criar Membro", type="primary")

        if submitted:
            member_data = {
                'member_id': str(member_id).strip(),
                'nome': nome,
                'instrumento': instrumento,
                'email': email,
                'telefone': telefone,
                'ativo': ativo
            }

            validation_msg = get_validation_message('member', member_data)
            if isinstance(validation_msg, str) and validation_msg.startswith("OK:"):
                ok = data_writer.create_member(member_data)
                if ok:
                    st.success("Membro criado!")
                    st.rerun()
                else:
                    st.error("Erro ao criar membro (data_writer retornou False).")
            else:
                st.error(validation_msg if isinstance(validation_msg, str) else "Validação inválida.")


def render_merchandising_crud(data):
    """CRUD para merchandising"""
    st.subheader("Gerenciar Merchandising")

    action = st.radio(
        "Ação",
        ["Visualizar", "Adicionar"],
        horizontal=True,
        key="merch_action"
    )

    merch_df = _normalize_columns(data.get('merchandising', pd.DataFrame()))

    if action == "Visualizar":
        if not merch_df.empty:
            st.dataframe(merch_df, use_container_width=True, height=300)
            st.caption(f"Total: {len(merch_df)} registros")
        else:
            st.info("Nenhum registro de merchandising")

    elif action == "Adicionar":
        render_create_merchandising_form()


def render_create_merchandising_form():
    """Formulário para criar novo registro de merchandising"""
    st.markdown("### Novo Registro de Merchandising")

    with st.form("create_merch_form"):
        col1, col2 = st.columns(2)

        with col1:
            merch_id = st.text_input("ID", value=f"MERCH-{datetime.now().strftime('%Y%m%d%H%M%S')}")
            data_merch = st.date_input("Data", value=datetime.now().date())
            tipo = st.selectbox("Tipo", ["VENDA", "COMPRA"])
            produto = st.text_input("Produto")

        with col2:
            quantidade = st.number_input("Quantidade", min_value=1, value=1)
            valor_unitario = st.number_input("Valor Unitário (R$)", min_value=0.01, value=10.0)
            show_id = st.text_input("Show Relacionado (opcional)")
            observacao = st.text_area("Observações")

        valor_total = float(quantidade) * float(valor_unitario)
        st.info(f"Valor Total: R$ {valor_total:,.2f}")

        submitted = st.form_submit_button("Criar Registro", type="primary")

        if submitted:
            merch_data = {
                'id': str(merch_id).strip(),
                'data': datetime.combine(data_merch, datetime.min.time()),
                'tipo': tipo,
                'produto': produto,
                'quantidade': int(quantidade),
                'valor_unitario': float(valor_unitario),
                'valor_total': float(valor_total),
                'show_id': str(show_id).strip() if show_id else None,
                'observacao': observacao
            }

            validation_msg = get_validation_message('merchandising', merch_data)
            if isinstance(validation_msg, str) and validation_msg.startswith("OK:"):
                ok = data_writer.create_merchandising(merch_data)
                if ok:
                    st.success("Registro criado!")
                    st.rerun()
                else:
                    st.error("Erro ao criar registro (data_writer retornou False).")
            else:
                st.error(validation_msg if isinstance(validation_msg, str) else "Validação inválida.")
