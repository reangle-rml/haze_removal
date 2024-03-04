import streamlit as st
from pages.Upload import main
from pages.Gallery import gallery
from pages.Manual import manual
from pages.Streaming import camera

st.set_page_config(layout="centered") # set หน้า page เป็นความ centered (จอแคบ)
st.session_state.button = False # set state button ให้เป็น False เพื่อยกเลิก session สำหรับ ค้นหา ในหน้า Gallery
st.header(":rainbow[Welcome to Haze Removal Image Enchancement Perspective for IoT device]",) # แสดง header
