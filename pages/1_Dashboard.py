"""
VerifAI — Enterprise Information System Overview
"""

import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Overview — VerifAI", page_icon="🛡️", layout="wide", initial_sidebar_state="collapsed")

# Load CSS
_css_path = os.path.join("assets", "style.css")
if os.path.exists(_css_path):
    with open(_css_path) as _f:
        st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)

st.markdown(
    '<div class="saas-header">'
    '<div class="logo-badge">✨ VERIFAI SYSTEM</div>'
    '<h1>Information Intelligence Overview</h1>'
    '<p>Real-time cross-verification system and research overview.</p>'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="empty-state">'
    '<div class="empty-state-icon">🛡️</div>'
    '<h3>Enterprise Fact-Checking System</h3>'
    '<p>VerifAI provides real-time verification of claims against verified global press sources and official fact checks.</p>'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="saas-footer">'
    '<p>VerifAI Intelligence System &nbsp;•&nbsp; <a href="#">Privacy Policy</a> &nbsp;•&nbsp; <a href="#">Terms of Service</a> &nbsp;•&nbsp; Powered by Enterprise AI</p>'
    '</div>',
    unsafe_allow_html=True,
)