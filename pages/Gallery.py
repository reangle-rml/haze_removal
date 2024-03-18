import streamlit as st
from google.cloud import firestore
import cv2
import numpy as np
import matplotlib.pyplot as plt
import io
import base64
from streamlit_modal import Modal
import datetime
db = firestore.Client.from_service_account_json("firestore_key.json") # เชื่อมต่อกับ ฐานข้อมูล firebase จากไฟล์ firestore-key.json
global_search_date = None # กำหนดค่าตัวแปรให้เป็น None
global_time_start = None # กำหนดค่าตัวแปรให้เป็น None
global_time_end = None # กำหนดค่าตัวแปรให้เป็น None
modal = Modal(key="Image",title="Image info",max_width=744,padding=20) # กำหนด Modal หรือ form ที่ใช้สำหรับแสดงข้อมูลรูปภาพ

if 'result' not in st.session_state: # ถ้า session_state ไม่มีชื่อ button ให้ทำตามเงื่อนไข
    st.session_state.result = [] # กำหนดให้ session_state.button ให้เป็น False เพื่อกำหนดค่าเริ่มต้น

def base64_to_histogram(base64_image): # function ที่เปลี่ยนจาก base64 ให้เป็น histogram
    binary_image = base64.b64decode(base64_image) # ทำการแปลง base64 ให้เป็น binary
    image_np = np.frombuffer(binary_image, dtype=np.uint8) # สร้าง numpy array จาก buffer binary ด้วย unit8
    if len(image_np) != 320 * 240: # ถ้าขนาดรูป ไม่เท่ากับ 240*320 ให้ทำตามเงื่อนไข
        image_np = np.resize(image_np, (320, 240)) # แปลงขนาดรูปเป็น 320*240
    hist = np.histogram(image_np, bins=256, range=[0, 256]) # แสดง histogram ด้วยค่าสี 0 ถึง 256
    plt.plot(hist[0]) # แสดงกราฟ histogram
    plt.title('Histogram') # แสดง title
    plt.xlabel('Pixel Value') # กำหนด label ในแกน x ค่าของสี
    plt.ylabel('Frequency') # กำหนด label ในแกน y ให้เป็น จำนวนความถี่(จำนวนสี)
    img_bytes = io.BytesIO() # สร้าง object สำหรับเก็บรูป
    plt.savefig(img_bytes, format='png') # บันทึก histogram ลงใน object ที่สร้างไว้ และกำหนดเป็น png
    img_bytes.seek(0) # ทำการกำหนด cursor ไปที่ตำแหน่ง 0 เพื่อเตรียมพร้อมสำหรับการอ่านค่า
    plt.clf() # clear กราฟเพื่อเตรียมสำหรับการแสดงกราฟใหม่
    return img_bytes.getvalue() # return ค่าของ img_bytes เพื่อนำไปแสดงเป็นรูป

def filter_by_date(doc, selected_date):# function สำหรับกรองการค้นหาด้วยวัน รับค่า doc ที่เป็นตำแหน่งของฐานข้อมูล และ selected_date ที่เป็นข้อมูลวันที่กำหนดตอนค้นหา
    data = doc.to_dict() # ดึงข้อมูลจาก ฐานข้อมูล
    log_time = data.get("log",None) # ดึงข้อมูล log ถ้าไม่เจอให้ return None
    print(log_time) # print ค่า log_time
    if log_time: # ถ้า log_time ไม่ใช่ None
        log_date = log_time["date"].strftime("%Y-%m-%d") # ดึงข้อมูลจาก วัน จาก log_time แล้วแปลงเป็น format ปี-เดือน-วัน
        print(log_date) # print log_date
        print(selected_date) # print selected_date
        return log_date == selected_date.strftime("%Y-%m-%d") # ถ้าค่า log_date มีค่าเท่ากับ selected_date ให้ retrun True
    return False # ถ้าไม่เข้าเงื่อนไขให้ return False

def filter_by_time_start(doc, selected_time_start): # function สำหรับกรองการค้นหาด้วยวัน รับค่า doc ที่เป็นตำแหน่งของฐานข้อมูล และ selected_time_start ที่เป็นข้อมูลเวลาเริ่มที่กำหนดตอนค้นหา
    data = doc.to_dict() # ดึงข้อมูลจาก ฐานข้อมูล
    log_time = data.get("log",None) # ดึงข้อมูล log ถ้าไม่เจอให้ return None
    print(log_time) # print ค่า log_time
    if log_time: # ถ้า log_time ไม่ใช่ None
        log_date = log_time["date"].strftime("%H:%M:%S") # ดึงข้อมูลจาก วัน จาก log_time แล้วแปลงเป็น format ชั่วโมง:นาที:วินาที
        print(log_date) # print log_date
        print(selected_time_start)  # print selected_time_start
        return log_date >= selected_time_start.strftime("%H:%M:%S") # ถ้าค่า log_date มีค่ามากกว่าหรือเท่ากับ selected_time_start  ให้ retrun True
    return False # ถ้าไม่เข้าเงื่อนไขให้ return False

def filter_by_time_end(doc, selected_time_end): # function สำหรับกรองการค้นหาด้วยวัน รับค่า doc ที่เป็นตำแหน่งของฐานข้อมูล และ selected_time_end ที่เป็นข้อมูลเวลาสิ้นสุดที่กำหนดตอนค้นหา
    data = doc.to_dict() # ดึงข้อมูลจาก ฐานข้อมูล
    log_time = data.get("log",None) # ดึงข้อมูล log ถ้าไม่เจอให้ return None
    print(log_time) # print ค่า log_time
    if log_time: # ถ้า log_time ไม่ใช่ None
        log_date = log_time["date"].strftime("%H:%M:%S") # ดึงข้อมูลจาก วัน จาก log_time แล้วแปลงเป็น format ชั่วโมง:นาที:วินาที
        print(log_date) # print log_date
        print(selected_time_end) # print selected_time_end
        return log_date <= selected_time_end.strftime("%H:%M:%S") # ถ้าค่า log_date มีค่าน้อยกว่าหรือเท่ากับ selected_time_end ให้ retrun True
    return False # ถ้าไม่เข้าเงื่อนไขให้ return False

def gallery(): # function gallery คือ ฟังก์ชั่นหลักสำหรับหน้า Gallery
    global global_search_date, global_time_start, global_time_end, modal # กำหนดค่าตัวแปรที่ได้ประกาศเป็น global ไว้ก่อนหน้านี้
    st.set_page_config(layout="wide") # set หน้า page เป็นความ wide (จอกว้าง)
    st.title("Gallery Page") # แสดง title
    header = st.columns(5) # สร้าง column 4 ช่องสำหรับรองรับระบบค้นหา
   
    open_modals = []
    with header[0]:
        type_selection = st.selectbox('Choose the source of the image',('Upload','Camera'))
    with header[1]: # เลือก header index แรก
        global_search_date = st.date_input("Select Date",value=None) # สร้าง input ประเภท date โดยมีค่าเริ่มต้นเป็น None เก็บไว้ที่ global_search_date
        if global_search_date: # ถ้า global_search_date มีการกำหนดค่าให้ทำตามเงื่อนไข
            button_check = False # กำหนดให้ button_check เป็น False
        else: # ไม่เข้าเงื่อนไขข้างต้น
            button_check = True # กำหนดให้ button_check เป็น True

    with header[2]: # เลือก header index สอง
        global_time_start = st.time_input("Time Start",key="time_start",value=None,disabled=button_check,step=1800) # สร้าง input ประเภท time โดยมีค่าเริ่มต้นเป็น None และให้การเปิด-ปิดการใช้งานเป็นไปตามตัวแปร button_check และเก็บไว้ที่ global_time_start
        if global_time_start and global_search_date: # ถ้า global_time_start และ global_search_date มีการกำหนดค่าให้ทำตามเงื่อนไข
            button_check2 = False # กำหนดให้ button_check2 เป็น False
        else: # ไม่เข้าเงื่อนไขข้างต้น
            button_check2 = True # กำหนดให้ button_check2 เป็น True
     
    with header[3]: # เลือก header index สาม
        global_time_end = st.time_input("Time End",key="time_end",value=None,disabled=button_check2) # สร้าง input ประเภท time โดยมีค่าเริ่มต้นเป็น None และให้การเปิด-ปิดการใช้งานเป็นไปตามตัวแปร button_check2 และเก็บไว้ที่ global_time_end
    with header[4]: # เลือก header index สี่
        st.write("") # สร้างการเว้นบรรทัด
        st.write("") # สร้างการเว้นบรรทัด
        search_button=st.button("Search",use_container_width=True) # สร้างปุ่มสำหรับค้นหา เก็บไว้ที่ serach_button
     # สร้างเส้นทางอ้างอิงไปยัง Images ในฐานข้อมูล
    
    col = st.columns(6) # สร้าง column 6 ช่องสำหรับรองรับรูปที่จะนำมาแสดง

    if type_selection=='Upload':
        collection_ref1 = db.collection("Images_upload")
    elif type_selection=='Camera':
        collection_ref1 = db.collection("Images_camera")
    docs1 = collection_ref1.stream() # ดึงข้อมูลจากเส้นทางอ้างอิง
    if(search_button):
        st.session_state.result = []
        for i, doc in enumerate(docs1): # ลูปตามจำนวนข้อมูลในฐานข้อมูลจากเส้นทางอ้างอิง
                    data = doc.to_dict() # ดึงข้อมูลจากเส้นทางอ้างอิง
                    if global_search_date is not None: # ถ้า global_search_date ไม่ใช่ค่า None 
                        if filter_by_date(doc, global_search_date): # ถ้าผ่านเงื่อนไขของ ฟังก์ชั่น filter_by_date จะ return ค่า true 
                            if global_time_start is not None and filter_by_time_start(doc, global_time_start): # ถ้า global_time_start ไม่ใช่ค่า None ผ่านเงื่อนไขของ ฟังก์ชั่น filter_by_date จะ return ค่า true 
                                if global_time_end is not None and filter_by_time_end(doc, global_time_end): # ถ้า global_time_end ไม่ใช่ค่า None ผ่านเงื่อนไขของ ฟังก์ชั่น filter_by_date จะ return ค่า true 
                                    st.session_state.result.append(data) # เพิ่มข้อมูล data ที่ผ่านเงื่อนไขลงใน filtered_images เพื่อนำไปแสดงผลลัพธ์การค้นหา
                                elif global_time_end is None: # ถ้า global_time_end เป็นค่า None 
                                    st.session_state.result.append(data) # เพิ่มข้อมูล data ที่ผ่านเงื่อนไขลงใน filtered_images เพื่อนำไปแสดงผลลัพธ์การค้นหา
                            elif global_time_start is None and global_time_end is None: # ถ้า global_time_start เป็นค่า None 
                                st.session_state.result.append(data) # เพิ่มข้อมูล data ที่ผ่านเงื่อนไขลงใน filtered_images เพื่อนำไปแสดงผลลัพธ์การค้นหา
                    else: # ถ้าไม่มีการกำหนดค่า global_serach_date จะทำตามเงื่อนไข
                        st.session_state.result.append(data) # เก็บข้อมูลทุกอย่าง
                    search_button=False
    if st.session_state.result: # ถ้า search_button หรือ st.session_state.button เป็น True

        with st.spinner("Loading Images..."): # ทำการโชว์การหมุนวน เพื่อแสดงว่า กำลังโหลด
            for i, data in enumerate(st.session_state.result): # ลูปตามจำนวน filtered_images             
                    image_before = data.get("img_original", None) # ดึงค่า img_original มาจากฐานข้อมูล หากไม่มีให้เป็น None เก็บไว้ที่ image_before
                    unique_identifier = data.get('log', {}).get('date', None)
                    image_removed = data.get("img_removed", None) # ดึงค่า img_removed มาจากฐานข้อมูล หากไม่มีให้เป็น None เก็บไว้ที่ image_removed
                    log_time = data.get("log", {}).get("date", None)
                    log_time = log_time + datetime.timedelta(hours=7)  # เพิ่ม 7 ชั่วโมงเพื่อแปลงเป็นเวลาท้องถิ่น (UTC+7)
                    show_date = log_time.strftime("Date %Y-%m-%d") # ดึงค่า date จาก log_time แล้วแปลงเป็น ปี-เดือน-วัน เก็บไว้ที่ show_date
                    show_time = log_time.strftime("Time %H:%M:%S") # ดึงค่า date จาก log_time แล้วแปลงเป็น ชั่วโมง-นาที-วินาทีเก็บไว้ที่ show_time
                    if i % 6 == 0: # ถ้า i หรือจำนวนรูปมีจำนวนที่ หาร 6 แล้วมีเศษ = 0 จะเข้าเงื่อนไข
                        col = st.columns(6) # สร้าง column ใหม่ 6 ช่องสำหรับรองรับรูปที่จะนำมาแสดง
                    if image_before: # ถ้ามีข้อมูลในตัวแปร image_before
                        with col[i%6]: # เลือก col ในตำแหน่งที่ได้จากการนำ i ไปหาร 6 แล้วได้เศษ เลือกใช้ตำแหน่งจาก เศษของผลหาร 
                                st.image(image_removed,use_column_width=True) # แสดงรูปภาพที่ผ่านการลบหมอกแล้ว โดยมีกว้้าง = width_im ที่กำหนด
                                
                                open_modal = st.button(label=f'Details',key=unique_identifier,use_container_width=True) # สร้างปุ่ม Details โดยมี key เป็น Details ตามด้วยค่าของ i ในปัจจุบัน
                        if open_modal:
                            with modal.container(): # แสดง modal ขึ้นมาเป็นหน้าจอเพื่อแสดงข้อมูลต่าง ๆ
                                col1, col2 = st.columns(2) # สร้าง column 2 ช่องเพื่อกำหนดโครงสร้างการแสดงรูป
                                col1.image(image_before,use_column_width=True) # แสดงรูปภาพต้นฉบับ โดยมีความกว้างเต็ม column
                                col1.image(image=base64_to_histogram(image_before),use_column_width=True) # แสดง histogram จากรูปภาพต้นฉบับ โดยมีความกว้างเต็ม column
                                col2.image(image_removed,use_column_width=True) # แสดงรูปภาพหลังลบหมอก โดยมีความกว้างเต็ม column
                                col2.image(image=base64_to_histogram(image_removed),use_column_width=True) # แสดง histogram จากรูปภาพหลังลบหมอก โดยมีความกว้างเต็ม column
                                st.write(show_date) # แสดงวันเดือนปี ที่เพิ่มข้อมูล
                                st.write(show_time) # แสดงเวลา ที่ทำการเพิ่มข้อมูล
            
                                               
    
                                                              
if __name__ == "__main__":
    gallery() # เรียกใช้ function manual() 
