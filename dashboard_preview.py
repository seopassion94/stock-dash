import streamlit as st
from dashboard_ui import render_dashboard

st.set_page_config(page_title="나의 주식 대시보드", page_icon="📊", layout="wide")
render_dashboard(sample=True)
