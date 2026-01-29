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
    st.title("Rockbuzz Finance - Dashboard")
    
    # Carregar dados
    with st.spinner("Carregando dados..."):
        data = data_loader.load_all_data()
    
    if not data or 'transactions' not in data:
        st.error("Nao foi possivel carregar os dados financeiros.")
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
    st.title("Receitas vs Despesas")
    
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
    """Página de análise detalhada de despesas - Visual Melhorado"""
    st.title("Despesas Detalhadas")
    
    # Carregar dados
    with st.spinner("Carregando dados..."):
        data = data_loader.load_all_data()
    
    if not data or 'transactions' not in data:
        st.error("Nao foi possivel carregar os dados")
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
    maior_despesa = despesas['valor'].max() if 'valor' in despesas.columns else 0
    
    # KPI Cards com visual melhorado
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                    padding: 20px; border-radius: 10px; border-left: 4px solid #f85149;">
            <p style="color: #8b949e; margin: 0; font-size: 0.85rem;">TOTAL DESPESAS</p>
            <h2 style="color: #f85149; margin: 5px 0;">R$ {total_despesas:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                    padding: 20px; border-radius: 10px; border-left: 4px solid #58a6ff;">
            <p style="color: #8b949e; margin: 0; font-size: 0.85rem;">MEDIA POR DESPESA</p>
            <h2 style="color: #58a6ff; margin: 5px 0;">R$ {media_despesas:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                    padding: 20px; border-radius: 10px; border-left: 4px solid #a371f7;">
            <p style="color: #8b949e; margin: 0; font-size: 0.85rem;">QUANTIDADE</p>
            <h2 style="color: #a371f7; margin: 5px 0;">{qtd_despesas}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                    padding: 20px; border-radius: 10px; border-left: 4px solid #d29922;">
            <p style="color: #8b949e; margin: 0; font-size: 0.85rem;">MAIOR DESPESA</p>
            <h2 style="color: #d29922; margin: 5px 0;">R$ {maior_despesa:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.markdown("""
        <div style="
            background: linear-gradient(145deg, #161b22 0%, #21262d 100%);
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
        ">
            <h4 style="color: #c9d1d9; margin: 0 0 0.5rem 0; font-size: 14px;">
                Despesas por Subcategoria
            </h4>
        """, unsafe_allow_html=True)
        
        if 'subcategoria' in despesas.columns:
            despesas_por_subcategoria = despesas.groupby('subcategoria')['valor'].sum().sort_values(ascending=False).head(10)
            
            if not despesas_por_subcategoria.empty:
                fig_bar = go.Figure(go.Bar(
                    x=despesas_por_subcategoria.values,
                    y=despesas_por_subcategoria.index,
                    orientation='h',
                    marker=dict(
                        color=despesas_por_subcategoria.values,
                        colorscale='Reds',
                        showscale=False
                    ),
                    text=[f'R$ {v:,.2f}' for v in despesas_por_subcategoria.values],
                    textposition='auto'
                ))
                fig_bar.update_layout(
                    template='plotly_dark',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    height=350,
                    yaxis=dict(autorange="reversed"),
                    xaxis_title="Valor (R$)",
                    yaxis_title=""
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("Sem dados de subcategoria")
        elif 'categoria' in despesas.columns:
            despesas_por_categoria = despesas.groupby('categoria')['valor'].sum().sort_values(ascending=False).head(10)
            
            if not despesas_por_categoria.empty:
                fig_bar = go.Figure(go.Bar(
                    x=despesas_por_categoria.values,
                    y=despesas_por_categoria.index,
                    orientation='h',
                    marker=dict(
                        color=despesas_por_categoria.values,
                        colorscale='Reds',
                        showscale=False
                    ),
                    text=[f'R$ {v:,.2f}' for v in despesas_por_categoria.values],
                    textposition='auto'
                ))
                fig_bar.update_layout(
                    template='plotly_dark',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    height=350,
                    yaxis=dict(autorange="reversed"),
                    xaxis_title="Valor (R$)",
                    yaxis_title=""
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("Sem dados de categoria")
        else:
            st.info("Dados de categoria nao disponiveis")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col_chart2:
        st.markdown("""
        <div style="
            background: linear-gradient(145deg, #161b22 0%, #21262d 100%);
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
        ">
            <h4 style="color: #c9d1d9; margin: 0 0 0.5rem 0; font-size: 14px;">
                Distribuicao por Categoria
            </h4>
        """, unsafe_allow_html=True)
        
        if 'categoria' in despesas.columns:
            despesas_por_categoria = despesas.groupby('categoria')['valor'].sum().sort_values(ascending=False)
            
            if not despesas_por_categoria.empty:
                colors = ['#f85149', '#ff7b72', '#ffa198', '#d29922', '#a371f7', '#58a6ff', '#39c5cf']
                fig_pie = go.Figure(go.Pie(
                    values=despesas_por_categoria.values,
                    labels=despesas_por_categoria.index,
                    hole=0.5,
                    marker=dict(colors=colors[:len(despesas_por_categoria)]),
                    textinfo='percent+label',
                    textposition='outside'
                ))
                fig_pie.update_layout(
                    template='plotly_dark',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    height=350,
                    showlegend=False
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("Sem dados de categoria")
        else:
            st.info("Dados de categoria nao disponiveis")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style="
        background: linear-gradient(145deg, #161b22 0%, #21262d 100%);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
    ">
        <h4 style="color: #c9d1d9; margin: 0 0 0.5rem 0; font-size: 14px;">
            Top 10 Shows por Despesas
        </h4>
    """, unsafe_allow_html=True)
    
    if 'show_id' in despesas.columns or 'descricao' in despesas.columns:
        group_col = 'show_id' if 'show_id' in despesas.columns else 'descricao'
        despesas_por_show = despesas.groupby(group_col)['valor'].sum().sort_values(ascending=False).head(10)
        
        if not despesas_por_show.empty:
            fig_shows = go.Figure(go.Bar(
                x=despesas_por_show.values,
                y=despesas_por_show.index.astype(str),
                orientation='h',
                marker=dict(
                    color=despesas_por_show.values,
                    colorscale='Oranges',
                    showscale=False
                ),
                text=[f'R$ {v:,.2f}' for v in despesas_por_show.values],
                textposition='auto'
            ))
            fig_shows.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=400,
                yaxis=dict(autorange="reversed"),
                xaxis_title="Valor (R$)",
                yaxis_title=""
            )
            st.plotly_chart(fig_shows, use_container_width=True)
        else:
            st.info("Sem dados de shows")
    else:
        st.info("Dados de shows nao disponiveis")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Tabela detalhada com estilo
    st.markdown("### Todas as Despesas")
    
    despesas_display = despesas.copy()
    if 'data' in despesas_display.columns:
        despesas_display['data'] = pd.to_datetime(despesas_display['data'], errors='coerce').dt.strftime('%d/%m/%Y')
    
    colunas_possiveis = ['data', 'categoria', 'descricao', 'valor', 'payment_status']
    colunas_disponiveis = [col for col in colunas_possiveis if col in despesas_display.columns]
    
    if colunas_disponiveis:
        st.dataframe(
            despesas_display[colunas_disponiveis].sort_values('valor' if 'valor' in despesas_display.columns else 'data', ascending=False),
            use_container_width=True,
            height=400
        )
    
    # Botao de exportacao
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
    with col_btn1:
        if st.button("Exportar para Excel", use_container_width=True):
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
    """Página de análise detalhada de receitas - Visual Melhorado"""
    st.title("Receitas Detalhadas")
    
    # Carregar dados
    with st.spinner("Carregando dados..."):
        data = data_loader.load_all_data()
    
    if not data or 'transactions' not in data:
        st.error("Nao foi possivel carregar os dados")
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
    maior_receita = receitas['valor'].max() if 'valor' in receitas.columns else 0
    
    # KPI Cards com visual melhorado
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                    padding: 20px; border-radius: 10px; border-left: 4px solid #3fb950;">
            <p style="color: #8b949e; margin: 0; font-size: 0.85rem;">TOTAL RECEITAS</p>
            <h2 style="color: #3fb950; margin: 5px 0;">R$ {total_receitas:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                    padding: 20px; border-radius: 10px; border-left: 4px solid #58a6ff;">
            <p style="color: #8b949e; margin: 0; font-size: 0.85rem;">MEDIA POR RECEITA</p>
            <h2 style="color: #58a6ff; margin: 5px 0;">R$ {media_receitas:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                    padding: 20px; border-radius: 10px; border-left: 4px solid #a371f7;">
            <p style="color: #8b949e; margin: 0; font-size: 0.85rem;">QUANTIDADE</p>
            <h2 style="color: #a371f7; margin: 5px 0;">{qtd_receitas}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                    padding: 20px; border-radius: 10px; border-left: 4px solid #d29922;">
            <p style="color: #8b949e; margin: 0; font-size: 0.85rem;">MAIOR RECEITA</p>
            <h2 style="color: #d29922; margin: 5px 0;">R$ {maior_receita:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Receitas por show com visual melhorado
    if 'show_id' in receitas.columns:
        col_chart1, col_chart2 = st.columns(2)
        
        receitas_por_show = receitas.groupby('show_id')['valor'].sum().sort_values(ascending=False)
        
        if not receitas_por_show.empty:
            with col_chart1:
                # Gráfico de barras com tema dark
                fig_bar = go.Figure(go.Bar(
                    x=receitas_por_show.head(10).index.astype(str),
                    y=receitas_por_show.head(10).values,
                    marker=dict(
                        color=receitas_por_show.head(10).values,
                        colorscale='Greens',
                        showscale=False
                    ),
                    text=[f'R$ {v:,.0f}' for v in receitas_por_show.head(10).values],
                    textposition='outside'
                ))
                fig_bar.update_layout(
                    title="Top 10 Shows por Receita",
                    template='plotly_dark',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    height=400,
                    xaxis_title="Show ID",
                    yaxis_title="Receita (R$)"
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            
            with col_chart2:
                # Gráfico de pizza (donut) com tema dark
                colors = ['#3fb950', '#56d364', '#7ee787', '#aff5b4', '#dafbe1']
                fig_pie = go.Figure(go.Pie(
                    values=receitas_por_show.head(5).values,
                    labels=receitas_por_show.head(5).index.astype(str),
                    hole=0.5,
                    marker=dict(colors=colors[:len(receitas_por_show.head(5))]),
                    textinfo='percent+label',
                    textposition='outside'
                ))
                fig_pie.update_layout(
                    title="Top 5 Shows (Participacao)",
                    template='plotly_dark',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    height=400,
                    showlegend=False
                )
                st.plotly_chart(fig_pie, use_container_width=True)
    
    # Análise por categoria com visual melhorado
    if 'categoria' in receitas.columns:
        receitas_por_categoria = receitas.groupby('categoria')['valor'].sum().sort_values(ascending=False)
        
        if not receitas_por_categoria.empty:
            col_cat1, col_cat2 = st.columns(2)
            
            with col_cat1:
                # Cards de categoria
                st.markdown("### Receitas por Categoria")
                for i, (categoria, valor) in enumerate(receitas_por_categoria.head(5).items()):
                    percentual = (valor / total_receitas * 100) if total_receitas > 0 else 0
                    color = ['#3fb950', '#58a6ff', '#a371f7', '#d29922', '#39c5cf'][i % 5]
                    st.markdown(f"""
                    <div style="background: #161b22; padding: 12px; border-radius: 8px; 
                                margin-bottom: 8px; border-left: 3px solid {color};">
                        <span style="color: #8b949e; font-size: 0.85rem;">{categoria}</span><br/>
                        <span style="color: {color}; font-size: 1.2rem; font-weight: bold;">R$ {valor:,.2f}</span>
                        <span style="color: #8b949e; font-size: 0.85rem;"> ({percentual:.1f}%)</span>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col_cat2:
                # Gráfico de barras horizontal
                fig_cat = go.Figure(go.Bar(
                    x=receitas_por_categoria.values,
                    y=receitas_por_categoria.index,
                    orientation='h',
                    marker=dict(
                        color=receitas_por_categoria.values,
                        colorscale='Greens',
                        showscale=False
                    ),
                    text=[f'R$ {v:,.2f}' for v in receitas_por_categoria.values],
                    textposition='auto'
                ))
                fig_cat.update_layout(
                    title="Distribuicao por Categoria",
                    template='plotly_dark',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    height=350,
                    yaxis=dict(autorange="reversed"),
                    xaxis_title="Valor (R$)",
                    yaxis_title=""
                )
                st.plotly_chart(fig_cat, use_container_width=True)
    
    # Evolucao temporal das receitas
    if 'data' in receitas.columns:
        receitas_temp = receitas.copy()
        receitas_temp['data'] = pd.to_datetime(receitas_temp['data'], errors='coerce')
        receitas_temp = receitas_temp.dropna(subset=['data'])
        
        if not receitas_temp.empty:
            receitas_temp['mes'] = receitas_temp['data'].dt.to_period('M').astype(str)
            receitas_mensal = receitas_temp.groupby('mes')['valor'].sum().reset_index()
            
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(
                x=receitas_mensal['mes'],
                y=receitas_mensal['valor'],
                mode='lines+markers',
                fill='tozeroy',
                line=dict(color='#3fb950', width=3),
                marker=dict(size=8, color='#3fb950'),
                fillcolor='rgba(63, 185, 80, 0.2)'
            ))
            fig_line.update_layout(
                title="Evolucao Mensal das Receitas",
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=300,
                xaxis_title="Mes",
                yaxis_title="Valor (R$)"
            )
            st.plotly_chart(fig_line, use_container_width=True)
    
    # Tabela detalhada
    st.markdown("### Todas as Receitas")
    
    receitas_display = receitas.copy()
    if 'data' in receitas_display.columns:
        receitas_display['data'] = pd.to_datetime(receitas_display['data'], errors='coerce').dt.strftime('%d/%m/%Y')
    
    colunas_possiveis = ['data', 'descricao', 'valor', 'show_id', 'categoria']
    colunas_disponiveis = [col for col in colunas_possiveis if col in receitas_display.columns]
    
    if colunas_disponiveis:
        st.dataframe(
            receitas_display[colunas_disponiveis].sort_values('valor' if 'valor' in receitas_display.columns else 'data', ascending=False),
            use_container_width=True,
            height=400
        )
    
    # Botao de exportacao
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
    with col_btn1:
        if st.button("Exportar para Excel", key="export_receitas", use_container_width=True):
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
