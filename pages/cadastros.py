"""
Página de cadastro de registros (CRUD)
Implementa formulários para todas as entidades
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import uuid

from core.data_loader import data_loader
from core.data_writer import data_writer
from core.validators import get_validation_message
from core.auth import check_permission
from core.constants import (
    TransactionType, PaymentStatus, ShowStatus, PayoutModel,
    OPERATIONAL_EXPENSE_CATEGORIES
)

def main():
    """Página principal de cadastros"""
    st.title("📝 Cadastro de Registros")
    
    if not check_permission("membro"):
        st.error("Você não tem permissão para acessar esta página.")
        return
    
    with st.spinner("Carregando dados..."):
        data = data_loader.load_all_data()
    
    tabs = st.tabs([
        "🎸 Shows",
        "💰 Transações",
        "📊 Regras de Rateio",
        "👥 Membros",
        "📦 Merchandising"
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


def render_shows_crud(data):
    """CRUD para shows"""
    st.subheader("🎸 Gerenciar Shows")
    
    action = st.radio(
        "Ação",
        ["Visualizar", "Adicionar", "Editar", "Excluir"],
        horizontal=True,
        key="shows_action"
    )
    
    shows_df = data.get('shows', pd.DataFrame())
    
    if action == "Visualizar":
        if not shows_df.empty:
            st.dataframe(shows_df, use_container_width=True, height=400)
            st.caption(f"Total: {len(shows_df)} shows")
        else:
            st.info("Nenhum show cadastrado")
    
    elif action == "Adicionar":
        render_create_show_form()
    
    elif action == "Editar":
        if not shows_df.empty:
            show_id = st.selectbox(
                "Selecione o show",
                shows_df['show_id'].tolist(),
                key="edit_show_select"
            )
            if show_id:
                show_data = shows_df[shows_df['show_id'] == show_id].iloc[0].to_dict()
                render_edit_show_form(show_data)
        else:
            st.info("Nenhum show para editar")
    
    elif action == "Excluir":
        if not shows_df.empty:
            show_id = st.selectbox(
                "Selecione o show para excluir",
                shows_df['show_id'].tolist(),
                key="delete_show_select"
            )
            if show_id:
                show_data = shows_df[shows_df['show_id'] == show_id].iloc[0]
                st.warning(f"Show: {show_data.get('casa', '')} - {show_data.get('cidade', '')}")
                
                if st.button("Confirmar Exclusão", type="primary", key="confirm_delete_show"):
                    if data_writer.delete_show(show_id):
                        st.rerun()
        else:
            st.info("Nenhum show para excluir")


def render_create_show_form():
    """Formulário para criar novo show"""
    st.markdown("### Novo Show")
    
    with st.form("create_show_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            show_id = st.text_input(
                "ID do Show",
                value=f"SHOW-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
            )
            data_show = st.date_input("Data do Show", value=datetime.now())
            casa = st.text_input("Casa/Local")
            cidade = st.text_input("Cidade")
        
        with col2:
            status = st.selectbox(
                "Status",
                [s.value for s in ShowStatus]
            )
            publico = st.number_input("Público Estimado", min_value=0, value=0)
            cache_acordado = st.number_input("Cachê Acordado (R$)", min_value=0.0, value=0.0)
            observacao = st.text_area("Observações")
        
        submitted = st.form_submit_button("Criar Show", type="primary")
        
        if submitted:
            show_data = {
                'show_id': show_id,
                'data_show': datetime.combine(data_show, datetime.min.time()),
                'casa': casa,
                'cidade': cidade,
                'status': status,
                'publico': publico,
                'cache_acordado': cache_acordado,
                'observacao': observacao
            }
            
            validation_msg = get_validation_message('show', show_data)
            if validation_msg.startswith("✅"):
                if data_writer.create_show(show_data):
                    st.rerun()
            else:
                st.error(validation_msg)


def render_edit_show_form(show_data):
    """Formulário para editar show existente"""
    st.markdown("### Editar Show")
    
    with st.form("edit_show_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            show_id = st.text_input("ID do Show", value=show_data.get('show_id', ''), disabled=True)
            
            current_date = show_data.get('data_show')
            if isinstance(current_date, str):
                current_date = datetime.strptime(current_date, '%Y-%m-%d')
            elif hasattr(current_date, 'date'):
                current_date = current_date.date()
            else:
                current_date = datetime.now().date()
            
            data_show = st.date_input("Data do Show", value=current_date)
            casa = st.text_input("Casa/Local", value=show_data.get('casa', ''))
            cidade = st.text_input("Cidade", value=show_data.get('cidade', ''))
        
        with col2:
            status_options = [s.value for s in ShowStatus]
            current_status = show_data.get('status', 'CONFIRMADO')
            status_index = status_options.index(current_status) if current_status in status_options else 0
            
            status = st.selectbox("Status", status_options, index=status_index)
            publico = st.number_input("Público", min_value=0, value=int(show_data.get('publico', 0) or 0))
            cache_acordado = st.number_input("Cachê Acordado (R$)", min_value=0.0, value=float(show_data.get('cache_acordado', 0) or 0))
            observacao = st.text_area("Observações", value=show_data.get('observacao', ''))
        
        submitted = st.form_submit_button("Salvar Alterações", type="primary")
        
        if submitted:
            updated_data = {
                'show_id': show_id,
                'data_show': datetime.combine(data_show, datetime.min.time()),
                'casa': casa,
                'cidade': cidade,
                'status': status,
                'publico': publico,
                'cache_acordado': cache_acordado,
                'observacao': observacao
            }
            
            validation_msg = get_validation_message('show', updated_data)
            if validation_msg.startswith("✅"):
                if data_writer.update_show(show_id, updated_data):
                    st.rerun()
            else:
                st.error(validation_msg)


def render_transactions_crud(data):
    """CRUD para transações"""
    st.subheader("💰 Gerenciar Transações")
    
    action = st.radio(
        "Ação",
        ["Visualizar", "Adicionar", "Editar", "Excluir"],
        horizontal=True,
        key="transactions_action"
    )
    
    transactions_df = data.get('transactions', pd.DataFrame())
    
    if action == "Visualizar":
        if not transactions_df.empty:
            col1, col2 = st.columns(2)
            with col1:
                tipo_filter = st.selectbox("Filtrar por tipo", ["Todos", "ENTRADA", "SAIDA"])
            with col2:
                status_filter = st.selectbox("Filtrar por status", ["Todos", "PAGO", "NÃO RECEBIDO"])
            
            filtered_df = transactions_df.copy()
            if tipo_filter != "Todos":
                filtered_df = filtered_df[filtered_df['tipo'] == tipo_filter]
            if status_filter != "Todos":
                filtered_df = filtered_df[filtered_df['payment_status'] == status_filter]
            
            st.dataframe(filtered_df, use_container_width=True, height=400)
            st.caption(f"Total: {len(filtered_df)} transações")
        else:
            st.info("Nenhuma transação cadastrada")
    
    elif action == "Adicionar":
        render_create_transaction_form(data)
    
    elif action == "Editar":
        if not transactions_df.empty:
            trans_id = st.selectbox(
                "Selecione a transação",
                transactions_df['id'].tolist(),
                key="edit_trans_select"
            )
            if trans_id:
                trans_data = transactions_df[transactions_df['id'] == trans_id].iloc[0].to_dict()
                render_edit_transaction_form(trans_data, data)
        else:
            st.info("Nenhuma transação para editar")
    
    elif action == "Excluir":
        if not transactions_df.empty:
            trans_id = st.selectbox(
                "Selecione a transação para excluir",
                transactions_df['id'].tolist(),
                key="delete_trans_select"
            )
            if trans_id:
                trans_data = transactions_df[transactions_df['id'] == trans_id].iloc[0]
                st.warning(f"Transação: {trans_data.get('descricao', '')} - R$ {trans_data.get('valor', 0):,.2f}")
                
                if st.button("Confirmar Exclusão", type="primary", key="confirm_delete_trans"):
                    if data_writer.delete_transaction(trans_id):
                        st.rerun()
        else:
            st.info("Nenhuma transação para excluir")


def render_create_transaction_form(data):
    """Formulário para criar nova transação"""
    st.markdown("### Nova Transação")
    
    shows_df = data.get('shows', pd.DataFrame())
    show_options = [""] + (shows_df['show_id'].tolist() if not shows_df.empty else [])
    
    with st.form("create_transaction_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            trans_id = st.text_input(
                "ID da Transação",
                value=f"TRANS-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            )
            data_trans = st.date_input("Data", value=datetime.now())
            tipo = st.selectbox("Tipo", [t.value for t in TransactionType])
            
            all_categories = ["CACHÊS-MÚSICOS"] + OPERATIONAL_EXPENSE_CATEGORIES
            categoria = st.selectbox("Categoria", all_categories)
            subcategoria = st.text_input("Subcategoria (opcional)")
        
        with col2:
            descricao = st.text_input("Descrição")
            valor = st.number_input("Valor (R$)", min_value=0.01, value=100.0)
            payment_status = st.selectbox("Status de Pagamento", [s.value for s in PaymentStatus])
            show_id = st.selectbox("Show Relacionado (opcional)", show_options)
            conta = st.text_input("Conta (opcional)")
        
        submitted = st.form_submit_button("Criar Transação", type="primary")
        
        if submitted:
            trans_data = {
                'id': trans_id,
                'data': datetime.combine(data_trans, datetime.min.time()),
                'tipo': tipo,
                'categoria': categoria,
                'subcategoria': subcategoria,
                'descricao': descricao,
                'valor': valor,
                'payment_status': payment_status,
                'show_id': show_id if show_id else None,
                'conta': conta
            }
            
            validation_msg = get_validation_message('transaction', trans_data)
            if validation_msg.startswith("✅"):
                if data_writer.create_transaction(trans_data):
                    st.rerun()
            else:
                st.error(validation_msg)


def render_edit_transaction_form(trans_data, data):
    """Formulário para editar transação existente"""
    st.markdown("### Editar Transação")
    
    shows_df = data.get('shows', pd.DataFrame())
    show_options = [""] + (shows_df['show_id'].tolist() if not shows_df.empty else [])
    
    with st.form("edit_transaction_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            trans_id = st.text_input("ID", value=trans_data.get('id', ''), disabled=True)
            
            current_date = trans_data.get('data')
            if isinstance(current_date, str):
                current_date = datetime.strptime(current_date, '%Y-%m-%d')
            elif hasattr(current_date, 'date'):
                current_date = current_date.date()
            else:
                current_date = datetime.now().date()
            
            data_trans = st.date_input("Data", value=current_date)
            
            tipo_options = [t.value for t in TransactionType]
            current_tipo = trans_data.get('tipo', 'ENTRADA')
            tipo_index = tipo_options.index(current_tipo) if current_tipo in tipo_options else 0
            tipo = st.selectbox("Tipo", tipo_options, index=tipo_index)
            
            all_categories = ["CACHÊS-MÚSICOS"] + OPERATIONAL_EXPENSE_CATEGORIES
            current_cat = trans_data.get('categoria', '')
            cat_index = all_categories.index(current_cat) if current_cat in all_categories else 0
            categoria = st.selectbox("Categoria", all_categories, index=cat_index)
            
            subcategoria = st.text_input("Subcategoria", value=trans_data.get('subcategoria', '') or '')
        
        with col2:
            descricao = st.text_input("Descrição", value=trans_data.get('descricao', ''))
            valor = st.number_input("Valor (R$)", min_value=0.01, value=float(trans_data.get('valor', 100) or 100))
            
            status_options = [s.value for s in PaymentStatus]
            current_status = trans_data.get('payment_status', 'PAGO')
            status_index = status_options.index(current_status) if current_status in status_options else 0
            payment_status = st.selectbox("Status de Pagamento", status_options, index=status_index)
            
            current_show = trans_data.get('show_id', '')
            show_index = show_options.index(current_show) if current_show in show_options else 0
            show_id = st.selectbox("Show Relacionado", show_options, index=show_index)
            
            conta = st.text_input("Conta", value=trans_data.get('conta', '') or '')
        
        submitted = st.form_submit_button("Salvar Alterações", type="primary")
        
        if submitted:
            updated_data = {
                'id': trans_id,
                'data': datetime.combine(data_trans, datetime.min.time()),
                'tipo': tipo,
                'categoria': categoria,
                'subcategoria': subcategoria,
                'descricao': descricao,
                'valor': valor,
                'payment_status': payment_status,
                'show_id': show_id if show_id else None,
                'conta': conta
            }
            
            validation_msg = get_validation_message('transaction', updated_data)
            if validation_msg.startswith("✅"):
                if data_writer.update_transaction(trans_id, updated_data):
                    st.rerun()
            else:
                st.error(validation_msg)


def render_payout_rules_crud(data):
    """CRUD para regras de rateio"""
    st.subheader("📊 Gerenciar Regras de Rateio")
    
    action = st.radio(
        "Ação",
        ["Visualizar", "Adicionar"],
        horizontal=True,
        key="payout_action"
    )
    
    rules_df = data.get('payout_rules', pd.DataFrame())
    
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
            vigencia_inicio = st.date_input("Início da Vigência", value=datetime.now())
            vigencia_fim = st.date_input("Fim da Vigência (opcional)", value=None)
        
        if pct_caixa + pct_musicos != 100:
            st.warning(f"Atenção: A soma dos percentuais é {pct_caixa + pct_musicos}% (deveria ser 100%)")
        
        submitted = st.form_submit_button("Criar Regra", type="primary")
        
        if submitted:
            rule_data = {
                'rule_id': rule_id,
                'nome_regra': nome_regra,
                'modelo': modelo,
                'pct_caixa': pct_caixa,
                'pct_musicos': pct_musicos,
                'ativa': ativa,
                'vigencia_inicio': datetime.combine(vigencia_inicio, datetime.min.time()),
                'vigencia_fim': datetime.combine(vigencia_fim, datetime.min.time()) if vigencia_fim else None
            }
            
            validation_msg = get_validation_message('payout_rule', rule_data)
            if validation_msg.startswith("✅"):
                if data_writer.create_payout_rule(rule_data):
                    st.rerun()
            else:
                st.error(validation_msg)


def render_members_crud(data):
    """CRUD para membros"""
    st.subheader("👥 Gerenciar Membros")
    
    action = st.radio(
        "Ação",
        ["Visualizar", "Adicionar"],
        horizontal=True,
        key="members_action"
    )
    
    members_df = data.get('members', pd.DataFrame())
    
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
            member_id = st.text_input(
                "ID do Membro",
                value=f"MEM-{str(uuid.uuid4())[:8].upper()}"
            )
            nome = st.text_input("Nome Completo")
            instrumento = st.text_input("Instrumento/Função")
        
        with col2:
            email = st.text_input("Email (opcional)")
            telefone = st.text_input("Telefone (opcional)")
            ativo = st.selectbox("Status", ["ATIVO", "INATIVO"])
        
        submitted = st.form_submit_button("Criar Membro", type="primary")
        
        if submitted:
            member_data = {
                'member_id': member_id,
                'nome': nome,
                'instrumento': instrumento,
                'email': email,
                'telefone': telefone,
                'ativo': ativo
            }
            
            validation_msg = get_validation_message('member', member_data)
            if validation_msg.startswith("✅"):
                st.success("Membro criado com sucesso!")
                st.rerun()
            else:
                st.error(validation_msg)


def render_merchandising_crud(data):
    """CRUD para merchandising"""
    st.subheader("📦 Gerenciar Merchandising")
    
    action = st.radio(
        "Ação",
        ["Visualizar", "Adicionar"],
        horizontal=True,
        key="merch_action"
    )
    
    merch_df = data.get('merchandising', pd.DataFrame())
    
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
            merch_id = st.text_input(
                "ID",
                value=f"MERCH-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            )
            data_merch = st.date_input("Data", value=datetime.now())
            tipo = st.selectbox("Tipo", ["VENDA", "COMPRA"])
            produto = st.text_input("Produto")
        
        with col2:
            quantidade = st.number_input("Quantidade", min_value=1, value=1)
            valor_unitario = st.number_input("Valor Unitário (R$)", min_value=0.01, value=10.0)
            show_id = st.text_input("Show Relacionado (opcional)")
            observacao = st.text_area("Observações")
        
        valor_total = quantidade * valor_unitario
        st.info(f"Valor Total: R$ {valor_total:,.2f}")
        
        submitted = st.form_submit_button("Criar Registro", type="primary")
        
        if submitted:
            merch_data = {
                'id': merch_id,
                'data': datetime.combine(data_merch, datetime.min.time()),
                'tipo': tipo,
                'produto': produto,
                'quantidade': quantidade,
                'valor_unitario': valor_unitario,
                'valor_total': valor_total,
                'show_id': show_id if show_id else None,
                'observacao': observacao
            }
            
            validation_msg = get_validation_message('merchandising', merch_data)
            if validation_msg.startswith("✅"):
                st.success("Registro de merchandising criado com sucesso!")
                st.rerun()
            else:
                st.error(validation_msg)
