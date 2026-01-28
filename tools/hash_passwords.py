from __future__ import annotations
import streamlit_authenticator as stauth

passwords = [
    "Japarangos@2024*",  # Murillo
    "Japarangos@2024*",  # Tay
    "Japarangos@2024*",  # Everton
    "Japarangos@2024*",  # Helio
    "Japarangos@2024*",  # Kiko
    "Japarangos@2024*",  # Naldo
]

hasher = stauth.Hasher()
for i, pwd in enumerate(passwords, 1):
    print(i, "=>", hasher.hash(pwd))
