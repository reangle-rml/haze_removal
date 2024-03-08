import streamlit as st

st.session_state.button = False # set state button ให้เป็น False เพื่อยกเลิก session สำหรับ ค้นหา ในหน้า Gallery

def manual(): # function manual คือฟังก์ชั่นหลักสำหรับ page Manual
    st.set_page_config(layout="wide") # set หน้า page เป็นความ wide (จอกว้าง)
    head=st.columns(3) # สร้าง columns 3 ช่อง
    with head[1]: # เลือกใช้ head index ตรงกลาง เพื่อทำให้ ข้อมูลด้านในอยู่ตรงกลางหน้าจอ
        st.header("Manual (คู่มือการใช้งาน)") # แสดง header
    col=st.columns(5) # สร้าง columns 5 ช่อง
    with col[1]: # เลือก col ที่เป็นตำแหน่ง 1 ซ้ายกลาง
        with st.container(border=True): # สร้างกล่อง Container เพื่อเก็บข้อมูล และตั้งเป็นแสดงขอบ
            st.subheader("Streaimg") # แสดง subheader
            st.divider() # สร้างเส้นใต้
            st.write("<center>ระบบ Live Streaming ที่ใช้สำหรับการตรวจจับหมอก สามารถกดปุ่ม Capture เพื่อบันทึกภาพนิ่งได้ เพื่อนำไปประมวลผลในการลบหมอก ระบบ Live Streaming จะทำการ Capture อัตโนมัติทุก 30 นาที</center>", unsafe_allow_html=True) # ใช้ unsafe_allow_html=True เพื่อให้สามารถใช้ css ในข้อมูลได้ ซึ่งก็คือ <center>
            st.divider() # สร้างเส้นใต้
            st.write('') # สร้างการเว้นบรรทัด
            st.image("images/capture1.png") # แสดงรูป capture1.png
    with col[2]: # เลือก col ที่เป็นตำแหน่ง 2 กลาง
        with st.container(border=True): # สร้างกล่อง Container เพื่อเก็บข้อมูล และตั้งเป็นแสดงขอบ
            st.subheader("Upload") #แสดง subheader
            st.divider() # สร้างเส้นใต้
            st.write("<center>ระบบ Upload ที่ใช้สำหรับการอัพโหลดรูปภาพที่ต้องการลบหมอกออก หลังจากการลบหมอกเสร็จสมบูรณ์ ระบบจะส่งรูปภาพไปเก็บไว้ที่ Gallery และแสดงรูปภาพ Histrogram เพื่อแสดงค่าก่อนและหลัง</center>", unsafe_allow_html=True) # ใช้ unsafe_allow_html=True เพื่อให้สามารถใช้ css ในข้อมูลได้ ซึ่งก็คือ <center>
            st.divider() # สร้างเส้นใต้
            st.write('') # สร้างการเว้นบรรทัด
            st.image("images/upload.png") # แสดงรูป upload.png
    with col[3]: # เลือก col ที่เป็นตำแหน่ง 3 ขวากลาง
        with st.container(border=True): # สร้างกล่อง Container เพื่อเก็บข้อมูล และตั้งเป็นแสดงขอบ
            st.subheader("Gallery") # แสดง subheader
            st.divider() # สร้างเส้นใต้
            st.write("<center>ระบบ Gallery ที่ใช้แสดงรูปภาพทั้งหมดที่ถูกลบหมอก จากระบบ Live Streaming และระบบ Upload รูปภาพ สามารถดูรายละเอียดของรูปภาพโดยการคลิก 'ดูรายละเอียด' ที่อยู่ใต้รูปภาพ<center>", unsafe_allow_html=True) # ใช้ unsafe_allow_html=True เพื่อให้สามารถใช้ css ในข้อมูลได้ ซึ่งก็คือ <center>
            st.divider() # สร้างเส้นใต้
            st.write('') # สร้างการเว้นบรรทัด
            st.image("images/gallery.png") # แสดงรูป gallery.png
    
if __name__ == "__main__":
    manual() # เรียกใช้ function manual() 


