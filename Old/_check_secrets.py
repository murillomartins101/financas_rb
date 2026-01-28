import streamlit as st
st.write("Tem 'gcp'?", "gcp" in st.secrets)
st.write("gcp:", dict(st.secrets.get("gcp", {})))
