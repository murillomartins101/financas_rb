# financas_rb/pages/cadastros.py
import streamlit as st

from core.auth import require_permission


def main(data=None):
    """
    Página de cadastros.
    Recebe `data` opcional para evitar reload.
    """
    # Permissão (ajuste a string se você usar outro padrão)
    require_permission("cadastros:view")

    st.title("Cadastros")

    # Debug opcional: mostra se data chegou
    # st.caption(f"Data recebido: {'sim' if data is not None else 'não'}")

    # ==========================
    # ✅ COLE AQUI SUA UI REAL
    # ==========================
    st.info("Página de Cadastros carregada com sucesso. Agora insira aqui os formulários/abas de cadastros.")

    # Exemplo de estrutura (remova se não quiser):
    tab1, tab2 = st.tabs(["Categorias", "Subcategorias"])

    with tab1:
        st.subheader("Cadastrar Categoria")
        nome = st.text_input("Nome da categoria")
        if st.button("Salvar categoria"):
            if not nome.strip():
                st.warning("Informe um nome.")
            else:
                st.success(f"Categoria '{nome}' salva (exemplo).")

    with tab2:
        st.subheader("Cadastrar Subcategoria")
        sub = st.text_input("Nome da subcategoria")
        cat = st.text_input("Categoria vinculada")
        if st.button("Salvar subcategoria"):
            if not sub.strip() or not cat.strip():
                st.warning("Preencha subcategoria e categoria.")
            else:
                st.success(f"Subcategoria '{sub}' vinculada à '{cat}' (exemplo).")
