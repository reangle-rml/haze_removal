import streamlit as st
from pages.Upload import main
from pages.Gallery import gallery
from pages.Manual import manual
from pages.Streaming import camera

st.set_page_config(layout="centered") # set หน้า page เป็นความ centered (จอแคบ)
st.session_state.button = False # set state button ให้เป็น False เพื่อยกเลิก session สำหรับ ค้นหา ในหน้า Gallery
st.header(":rainbow[Welcome to Haze Removal Image Enchancement Perspective for IoT device]",) # แสดง header

st.page_link("pages/Manual.py", label="Manual", icon="1️⃣") # pagelink กดเพื่อไปที่หน้า Manual (คู่มือ)
st.page_link("pages/Streaming.py", label="Streaming", icon="2️⃣") # pagelink กดเพื่อไปที่หน้า Streaming (ถ่ายทอดสด)
st.page_link("pages/Upload.py", label="Upload", icon="3️⃣") # pagelink กดเพื่อไปที่หน้า Upload (อัปโหลดรูป)
st.page_link("pages/Gallery.py", label="Gallery", icon="4️⃣") # pagelink กดเพื่อไปที่หน้า Gallery (คลังภาพ)