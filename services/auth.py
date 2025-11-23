import streamlit as st

def login_simulado():
    st.session_state.user = {"email": "dancadlim@gmail.com", "name": "Chefe"}
    st.rerun()

def logout():
    st.session_state.user = None
    st.session_state.active_project = None
    st.rerun()

def check_auth():
    if "user" not in st.session_state:
        st.session_state.user = None
    return st.session_state.user
