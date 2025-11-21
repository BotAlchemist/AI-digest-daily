import streamlit as st
import requests
import streamlit.components.v1 as components
import re
from datetime import datetime
import os

st.set_page_config(page_title="AI Daily Digest Viewer", layout="wide", page_icon="🗞")

# ---------------------------------------------
# CONFIG 
# ---------------------------------------------

API_KEY = os.getenv("API_KEY")
FOLDER_ID =os.getenv("FOLDER_ID")

LIST_URL = (
    f"https://www.googleapis.com/drive/v2/files"
    f"?q='{FOLDER_ID}'+in+parents&key={API_KEY}"
)

# ---------------------------------------------
# CACHE DECORATOR COMPAT
# ---------------------------------------------
try:
    cache = st.cache_data
except:
    cache = st.cache

# ---------------------------------------------
# SMART DATE PARSER
# ---------------------------------------------
def extract_date_from_filename(name):
    """
    Expects filenames like:
    AI-Digest-2025-11-21.html
    Returns datetime object
    """
    match = re.search(r"(\d{4})-(\d{2})-(\d{2})", name)
    if not match:
        return datetime.min
    y, m, d = match.groups()
    return datetime(int(y), int(m), int(d))


# ---------------------------------------------
# LIST DRIVE FILES
# ---------------------------------------------
@cache(ttl=300)
def list_html_files():
    res = requests.get(LIST_URL)
    if res.status_code != 200:
        st.error(f"Drive API Error: {res.text}")
        return []

    data = res.json()
    items = data.get("items", [])

    files = []
    for item in items:
        if item.get("mimeType") == "text/html":
            files.append({
                "id": item["id"],
                "name": item["title"],
                "date": extract_date_from_filename(item["title"])
            })

    # Sort by parsed date DESCENDING (newest first)
    files.sort(key=lambda x: x["date"], reverse=True)
    return files


# ---------------------------------------------
# DOWNLOAD HTML FILE
# ---------------------------------------------
def download_html(file_id):
    url = f"https://www.googleapis.com/drive/v2/files/{file_id}?alt=media&key={API_KEY}"
    return requests.get(url).text


# ---------------------------------------------
# UI
# ---------------------------------------------
# ---------------------------------------------
# CUSTOM CSS FOR NEWSPAPER LOOK
# ---------------------------------------------
st.markdown("""
<style>

    /* Global page style */
    body {
        background-color: #f2f0e9;
        font-family: 'Georgia', serif;
    }

    /* Newspaper-style header */
    .main-title {
        font-family: 'Georgia', serif;
        font-size: 46px;
        font-weight: bold;
        text-align: center;
        color: #2b2b2b;
        margin-top: 10px;
        margin-bottom: 5px;
    }

    .sub-title {
        text-align: center;
        font-size: 18px;
        font-style: italic;
        color: #5a5a5a;
        margin-bottom: 20px;
    }

    /* Classic newspaper divider */
    .divider {
        border-top: 3px solid #333;
        margin-top: 10px;
        margin-bottom: 25px;
    }

    /* Button styling */
    .stButton>button {
        background-color: #2d2d2d !important;
        color: #f7f7f7 !important;
        border-radius: 6px;
        font-size: 16px;
        padding: 0.6em 1.4em;
        border: 1px solid #000;
        font-family: 'Georgia', serif;
        letter-spacing: 0.5px;
    }

    .stButton>button:hover {
        background-color: #444 !important;
        color: white !important;
        transform: scale(1.02);
        border-color: #111;
    }

    /* Dropdown margin fix */
    .css-2ykyy6 {
        margin-top: -10px;
    }

</style>
""", unsafe_allow_html=True)

# ---------------------------------------------
# Newspaper Header
# ---------------------------------------------
st.markdown('<div class="main-title">AI Daily Digest Viewer</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Your curated AI news — formatted intelligently</div>', unsafe_allow_html=True)
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ---------------------------------------------
# UI — 3 Columns (3 : 1 : 1)
# ---------------------------------------------
files = list_html_files()

if not files:
    st.error("No HTML digest files found in Google Drive folder.")
    st.stop()

col1, col2, col3 = st.columns([3, 1, 1])

with col1:
    file_names = [f["name"] for f in files]
    selected = st.selectbox("Select a date:", file_names)

with col2:
    st.markdown("####")  # align button vertically
    load_clicked = st.button("View Newsletter")

with col3:
    st.markdown("####")
    about_clicked = st.button("About")

# ---------------------------------------------
# ABOUT POPUP SECTION
# ---------------------------------------------
if about_clicked:
    st.markdown("---")
    st.subheader("About This Website")

    st.markdown("""
This AI newspaper viewer summarizes daily AI news using **Google Gemini 2.5 Flash** and formats it into a clean newspaper-style HTML digest.

### How It Works  
- Emails are collected under a Gmail label  
- Google Apps Script extracts and cleans content  
- Gemini 2.5 Flash generates summarized newspaper-style HTML  
- Files are stored inside Google Drive  
- Streamlit loads and displays selected editions  

### Disclaimer  
- All articles are auto-generated by AI  
- Formatting may vary across editions  
- Some layout inconsistencies may occur  

###### Developed by Sumit Srivastava (@sumvast)  
    """)

    st.markdown("---")

# ---------------------------------------------
# LOAD SELECTED NEWSLETTER
# ---------------------------------------------
if load_clicked:
    file_id = next(f["id"] for f in files if f["name"] == selected)
    html_content = download_html(file_id)

    components.html(html_content, scrolling=True, height=9000)

