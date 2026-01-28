"""
Rockbuzz Finance - Dashboard Financeiro para Bandas
Arquivo principal da aplicação Streamlit
"""

import streamlit as st
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sys
import os

# Adiciona o diretório pages ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'pages'))

from core.auth import check_password, init_session_state
from core.ui_components import setup_page_config, render_sidebar, render_footer
from core.data_loader import data_loader
from core.metrics import FinancialMetrics

def main():
    """
    Função principal que inicializa a aplicação Streamlit
    Gerencia autenticação, sessão e navegação entre páginas
    """
    
    # Configuração inicial da página
    setup_page_config()
    
    # Inicializar estado da sessão
    init_session_state()
    
    # Verificar autenticação
    if not st.session_state.get("authenticated", False):
        if check_password():
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.stop()
    
    # Renderizar sidebar com logo e navegação
    render_sidebar()
    
    # Redirecionar para a página atual
    current_page = st.session_state.get("current_page", "Home")
    
    # Container principal
    main_container = st.container()
    
    with main_container:
        try:
            if current_page == "Home":
                show_home_page()
            elif current_page == "Shows":
                show_shows_page()
            elif current_page == "Transacoes":
                show_transacoes_page()
            elif current_page == "Relatorios":
                show_relatorios_page()
            elif current_page == "Cadastros":
                show_cadastros_page()
            elif current_page == "ReceitasDespesas":
                show_receitas_vs_despesas()
            elif current_page == "Despesas":
                show_despesas_detalhadas()
            elif current_page == "Receitas":
                show_receitas_detalhadas()
            else:
                # Fallback para Home
                st.session_state.current_page = "Home"
                st.rerun()
        except Exception as e:
            st.error(f"Erro ao carregar a página: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            st.info("Tente recarregar a página ou voltar para Home")
            if st.button("Voltar para Home"):
                st.session_state.current_page = "Home"
                st.rerun()
    
    # Renderizar rodapé
    render_footer()

def show_home_page():
    """Exibe a página inicial com KPIs principais"""
    try:
        # Importar a página Home
        from pages.home import main as home_main
        home_main()
    except ImportError as e:
        st.error(f"Erro ao importar módulo home: {str(e)}")
        show_basic_dashboard()
    except Exception as e:
        st.error(f"Erro ao carregar página Home: {str(e)}")
        show_basic_dashboard()

def show_basic_dashboard():
    """Dashboard básico como fallback"""
    st.title("🎸 Rockbuzz Finance - Dashboard")
    
    # Carregar dados
    with st.spinner("Carregando dados..."):
        data = data_loader.load_all_data()
    
    if not data or 'transactions' not in data:
        st.error("❌ Não foi possível carregar os dados financeiros.")
        return
    
    # KPIs básicos
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_entradas = data['transactions'][
            (data['transactions']['tipo'] == 'ENTRADA') & 
            (data['transactions']['payment_status'] == 'PAGO')
        ]['valor'].sum()
        st.metric("Total Receitas", f"R$ {total_entradas:,.2f}")
    
    with col2:
        total_despesas = data['transactions'][
            (data['transactions']['tipo'] == 'SAIDA') & 
            (data['transactions']['payment_status'] == 'PAGO')
        ]['valor'].sum()
        st.metric("Total Despesas", f"R$ {total_despesas:,.2f}")
    
    with col3:
        saldo = total_entradas - total_despesas
        st.metric("Saldo", f"R$ {saldo:,.2f}")

def show_shows_page():
    """Exibe a página de shows"""
    try:
        from pages.shows import main as shows_main
        shows_main()
    except ImportError:
        st.error("Módulo da página Shows não encontrado")
        st.info("Crie o arquivo pages/shows.py")
    except Exception as e:
        st.error(f"Erro ao carregar página Shows: {str(e)}")

def show_transacoes_page():
    """Exibe a página de transações"""
    try:
        from pages.transacoes import main as transacoes_main
        transacoes_main()
    except ImportError:
        st.error("Módulo da página Transações não encontrado")
        st.info("Crie o arquivo pages/transacoes.py")
    except Exception as e:
        st.error(f"Erro ao carregar página Transações: {str(e)}")

def show_relatorios_page():
    """Exibe a página de relatórios"""
    try:
        from pages.relatorios import main as relatorios_main
        relatorios_main()
    except ImportError:
        st.error("Módulo da página Relatórios não encontrado")
        st.info("Crie o arquivo pages/relatorios.py")
    except Exception as e:
        st.error(f"Erro ao carregar página Relatórios: {str(e)}")

def show_cadastros_page():
    """Exibe a página de cadastros"""
    try:
        from pages.cadastros import main as cadastros_main
        cadastros_main()
    except ImportError:
        st.error("Módulo da página Cadastros não encontrado")
        st.info("Crie o arquivo pages/cadastros.py")
    except Exception as e:
        st.error(f"Erro ao carregar página Cadastros: {str(e)}")

def show_receitas_vs_despesas():
    """Página de análise Receitas vs Despesas"""
    st.title("📉 Receitas vs Despesas")
    
    # Carregar dados
    with st.spinner("Carregando dados..."):
        data = data_loader.load_all_data()
    
    if not data or 'transactions' not in data:
        st.error("Não foi possível carregar os dados")
        return
    
    # Filtrar transações pagas
    transacoes_pagas = data['transactions'][
        data['transactions']['payment_status'] == 'PAGO'
    ].copy()
    
    if transacoes_pagas.empty:
        st.info("Nenhuma transação paga encontrada")
        return
    
    # Converter data para datetime se necessário
    if 'data' in transacoes_pagas.columns:
        transacoes_pagas['data'] = pd.to_datetime(transacoes_pagas['data'], errors='coerce')
    
    # Análise comparativa
    receitas = transacoes_pagas[transacoes_pagas['tipo'] == 'ENTRADA']
    despesas = transacoes_pagas[transacoes_pagas['tipo'] == 'SAIDA']
    
    total_receitas = receitas['valor'].sum() if 'valor' in receitas.columns else 0
    total_despesas = despesas['valor'].sum() if 'valor' in despesas.columns else 0
    saldo = total_receitas - total_despesas
    
    # KPIs comparativos
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Receitas", f"R$ {total_receitas:,.2f}")
    
    with col2:
        st.metric("Total Despesas", f"R$ {total_despesas:,.2f}")
    
    with col3:
        delta_percent = ((total_receitas - total_despesas) / total_receitas * 100) if total_receitas > 0 else 0
        st.metric("Saldo", f"R$ {saldo:,.2f}", 
                 delta=f"{delta_percent:.1f}%")
    
    # Gráfico comparativo
    fig = go.Figure(data=[
        go.Bar(name='Receitas', x=['Total'], y=[total_receitas], marker_color='#00CC96'),
        go.Bar(name='Despesas', x=['Total'], y=[total_despesas], marker_color='#EF553B')
    ])
    
    fig.update_layout(
        title="Comparação Receitas vs Despesas",
        barmode='group',
        height=400,
        template='plotly_white'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Análise temporal
    st.subheader("Evolução Temporal")
    
    # Agrupar por mês se tiver dados de data
    if 'data' in transacoes_pagas.columns and not transacoes_pagas['data'].isna().all():
        transacoes_pagas['mes'] = transacoes_pagas['data'].dt.to_period('M')
        
        evolucao_mensal = transacoes_pagas.groupby(['mes', 'tipo'])['valor'].sum().unstack().fillna(0)
        
        if not evolucao_mensal.empty and len(evolucao_mensal) > 1:
            fig2 = go.Figure()
            
            if 'ENTRADA' in evolucao_mensal.columns:
                fig2.add_trace(go.Scatter(
                    x=evolucao_mensal.index.astype(str),
                    y=evolucao_mensal['ENTRADA'],
                    name='Receitas',
                    line=dict(color='#00CC96', width=3)
                ))
            
            if 'SAIDA' in evolucao_mensal.columns:
                fig2.add_trace(go.Scatter(
                    x=evolucao_mensal.index.astype(str),
                    y=evolucao_mensal['SAIDA'],
                    name='Despesas',
                    line=dict(color='#EF553B', width=3)
                ))
            
            fig2.update_layout(
                title="Evolução Mensal",
                xaxis_title="Mês",
                yaxis_title="Valor (R$)",
                height=400,
                template='plotly_white'
            )
            
            st.plotly_chart(fig2, use_container_width=True)

def show_despesas_detalhadas():
    """Página de análise detalhada de despesas"""
    st.title("💸 Despesas Detalhadas")
    
    # Carregar dados
    with st.spinner("Carregando dados..."):
        data = data_loader.load_all_data()
    
    if not data or 'transactions' not in data:
        st.error("Não foi possível carregar os dados")
        return
    
    # Filtrar apenas despesas pagas
    despesas = data['transactions'][
        (data['transactions']['tipo'] == 'SAIDA') & 
        (data['transactions']['payment_status'] == 'PAGO')
    ].copy()
    
    if despesas.empty:
        st.info("Nenhuma despesa encontrada")
        return
    
    # Estatísticas gerais
    total_despesas = despesas['valor'].sum() if 'valor' in despesas.columns else 0
    media_despesas = despesas['valor'].mean() if 'valor' in despesas.columns else 0
    qtd_despesas = len(despesas)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Despesas", f"R$ {total_despesas:,.2f}")
    with col2:
        st.metric("Média por Despesa", f"R$ {media_despesas:,.2f}")
    with col3:
        st.metric("Quantidade", qtd_despesas)
    
    # Análise por categoria
    if 'categoria' in despesas.columns:
        st.subheader("Despesas por Categoria")
        
        despesas_por_categoria = despesas.groupby('categoria')['valor'].sum().sort_values(ascending=False)
        
        if not despesas_por_categoria.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Valor por Categoria:**")
                for categoria, valor in despesas_por_categoria.items():
                    percentual = (valor / total_despesas * 100) if total_despesas > 0 else 0
                    st.write(f"{categoria}: R$ {valor:,.2f} ({percentual:.1f}%)")
            
            with col2:
                # Gráfico de pizza
                fig = px.pie(
                    values=despesas_por_categoria.values,
                    names=despesas_por_categoria.index,
                    title="Distribuição por Categoria"
                )
                st.plotly_chart(fig, use_container_width=True)
    
    # Tabela detalhada
    st.subheader("Todas as Despesas")
    
    # Preparar dados para exibição
    despesas_display = despesas.copy()
    
    # Formatar datas se existirem
    if 'data' in despesas_display.columns:
        despesas_display['data'] = pd.to_datetime(despesas_display['data'], errors='coerce').dt.strftime('%d/%m/%Y')
    
    # Selecionar colunas disponíveis
    colunas_possiveis = ['data', 'categoria', 'descricao', 'valor', 'payment_status']
    colunas_disponiveis = [col for col in colunas_possiveis if col in despesas_display.columns]
    
    if colunas_disponiveis:
        st.dataframe(
            despesas_display[colunas_disponiveis].sort_values('valor' if 'valor' in despesas_display.columns else 'data', ascending=False),
            use_container_width=True,
            height=400
        )
    else:
        st.write(despesas_display)
    
    # Opção para download
    if st.button("📥 Exportar para Excel"):
        try:
            import io
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                despesas.to_excel(writer, sheet_name='Despesas', index=False)
            
            st.download_button(
                label="Baixar arquivo Excel",
                data=buffer.getvalue(),
                file_name=f"despesas_rockbuzz_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.error(f"Erro ao exportar: {str(e)}")

def show_receitas_detalhadas():
    """Página de análise detalhada de receitas"""
    st.title("💰 Receitas Detalhadas")
    
    # Carregar dados
    with st.spinner("Carregando dados..."):
        data = data_loader.load_all_data()
    
    if not data or 'transactions' not in data:
        st.error("Não foi possível carregar os dados")
        return
    
    # Filtrar apenas receitas pagas
    receitas = data['transactions'][
        (data['transactions']['tipo'] == 'ENTRADA') & 
        (data['transactions']['payment_status'] == 'PAGO')
    ].copy()
    
    if receitas.empty:
        st.info("Nenhuma receita encontrada")
        return
    
    # Estatísticas gerais
    total_receitas = receitas['valor'].sum() if 'valor' in receitas.columns else 0
    media_receitas = receitas['valor'].mean() if 'valor' in receitas.columns else 0
    qtd_receitas = len(receitas)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Receitas", f"R$ {total_receitas:,.2f}")
    with col2:
        st.metric("Média por Receita", f"R$ {media_receitas:,.2f}")
    with col3:
        st.metric("Quantidade", qtd_receitas)
    
    # Receitas por show
    if 'show_id' in receitas.columns:
        st.subheader("Receitas por Show")
        
        receitas_por_show = receitas.groupby('show_id')['valor'].sum().sort_values(ascending=False)
        
        if not receitas_por_show.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Top 10 Shows por Receita:**")
                for show_id, valor in receitas_por_show.head(10).items():
                    percentual = (valor / total_receitas * 100) if total_receitas > 0 else 0
                    st.write(f"Show {show_id}: R$ {valor:,.2f} ({percentual:.1f}%)")
            
            with col2:
                # Gráfico de barras
                fig = px.bar(
                    x=receitas_por_show.head(10).index.astype(str),
                    y=receitas_por_show.head(10).values,
                    title="Top 10 Shows por Receita"
                )
                fig.update_layout(xaxis_title="Show ID", yaxis_title="Receita (R$)")
                st.plotly_chart(fig, use_container_width=True)
    
    # Análise por categoria
    if 'categoria' in receitas.columns:
        st.subheader("Receitas por Categoria")
        
        receitas_por_categoria = receitas.groupby('categoria')['valor'].sum().sort_values(ascending=False)
        
        if not receitas_por_categoria.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                for categoria, valor in receitas_por_categoria.head(5).items():
                    percentual = (valor / total_receitas * 100) if total_receitas > 0 else 0
                    st.metric(categoria, f"R$ {valor:,.2f}", f"{percentual:.1f}%")
            
            with col2:
                fig = px.pie(
                    values=receitas_por_categoria.head(5).values,
                    names=receitas_por_categoria.head(5).index,
                    title="Top 5 Categorias de Receita"
                )
                st.plotly_chart(fig, use_container_width=True)
    
    # Tabela detalhada
    st.subheader("Todas as Receitas")
    
    # Preparar dados para exibição
    receitas_display = receitas.copy()
    
    # Formatar datas se existirem
    if 'data' in receitas_display.columns:
        receitas_display['data'] = pd.to_datetime(receitas_display['data'], errors='coerce').dt.strftime('%d/%m/%Y')
    
    # Selecionar colunas disponíveis
    colunas_possiveis = ['data', 'descricao', 'valor', 'show_id', 'categoria']
    colunas_disponiveis = [col for col in colunas_possiveis if col in receitas_display.columns]
    
    if colunas_disponiveis:
        st.dataframe(
            receitas_display[colunas_disponiveis].sort_values('valor' if 'valor' in receitas_display.columns else 'data', ascending=False),
            use_container_width=True,
            height=400
        )
    else:
        st.write(receitas_display)
    
    # Opção para download
    if st.button("📥 Exportar para Excel"):
        try:
            import io
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                receitas.to_excel(writer, sheet_name='Receitas', index=False)
            
            st.download_button(
                label="Baixar arquivo Excel",
                data=buffer.getvalue(),
                file_name=f"receitas_rockbuzz_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.error(f"Erro ao exportar: {str(e)}")

if __name__ == "__main__":
    main()