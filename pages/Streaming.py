import streamlit as st
from google.cloud import firestore
import base64
import cv2
import tempfile
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
from PIL import Image
from datetime import datetime
import io
from apscheduler.schedulers.background import BackgroundScheduler
import image_dehazer
import urllib.request
from firebase_admin import credentials, db

dab = firestore.Client.from_service_account_json("firestore_key.json") # เชื่อมต่อกับ ฐานข้อมูล firebase จากไฟล์ firestore-key.json 
cred = credentials.Certificate("firestore_key.json") # ยืนยันตัวตน firebase จากไฟล์ firestore-key.json
initialize_app(cred, {"databaseURL": "https://haze-remover-default-rtdb.asia-southeast1.firebasedatabase.app/"})
st.session_state.button = False # set state button ให้เป็น False เพื่อยกเลิก session สำหรับ ค้นหา ในหน้า Gallery
scheduler = BackgroundScheduler() # กำหนดตัวแปร ที่ใช้ในการทำงานเบื้องหลัง
document_ref = '' # กำหนดตัวแปร document_ref
collection_ref = dab.collection("Images") # สร้างเส้นทางอ้างอิงไปยัง Images ในฐานข้อมูล
live = db.reference("image_original") # สร้างเส้นทางอ้างอิงไปยัง image_original ไปยัง realtime database
ip_camera_url = "http://192.168.137.94/cam-lo.jpg" # กำหนด ip_camera_url
old_time = '' # กำหนดตัวแปร old_time 

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

def frame_to_base64(frame):
    _, buffer = cv2.imencode(".jpeg", frame)  # ทำการแปลง frame ให้เป็นรูปภาพ นามสกุล .jpeg ด้วย cv2 
    frame_bytes = BytesIO(buffer.tobytes()) # สร้าง Object จาก buffer แล้วเป็น bytes แล้วเก็บไว้ที่ frame_bytes
    encoded_string = base64.b64encode(frame_bytes.read()).decode("utf-8") # ทำการถอดรหัส frame ให้เป็น base64
    return "data:image/jpeg;base64," + encoded_string # return ค่า base64 ที่ทำการใส่ format base64 เข้าไป

def base64_encode_image(image_path): 
    with open(image_path, "rb") as image_file: # เปิดรูปภาพ image_path ในรูปแบบ rb
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8") #ทำการเข้ารหัสรูปภาพให้รูปภาพเปลี่ยนเป็น base64
    image = Image.open(io.BytesIO(base64.b64decode(encoded_string))) #เปลี่ยนรูปภาพจาก string ให้เป็น image
    resized_image = image.resize((320, 240)) # ปรับขนาดของรูปตามที่กำหนดไว้ในตัวแปร
    resized_binary = BytesIO() # สรา้ง object ขึ้นมาที่ resize_binary
    resized_image.save(resized_binary, format='jpeg') # บันทึก object ลงไปที่ resizeg_image ด้วย format jpeg
    resized_binary = base64.b64encode(resized_binary.getvalue()).decode("utf-8") # ถอดรหัสรูปภาพและเก็บค่าของรูปภาพไว้ที่ resized_binary ด้วย utf-8
    base64_original = "data:image/jpeg;base64,"+resized_binary # ใส่ baes64 format ลงไปในค่าจาก resized_binary
    return base64_original # return ค่า base64 ที่ใส่ format base64 เข้าไป

def base64_to_img(base64_image): # function ในการทำ base64 เป็นรูปภาพด้วยการรับค่า base64
    image_data = base64.b64decode(base64_image) # ทำการถอดรหัส base64 ให้เป็นรูปภาพแล้วเก็บไว้ที่ image_data
    nparr = np.frombuffer(image_data, np.uint8) # นำ image_data มาใช้ numpy ในการสร้างภาพ และเก็บไว้ที่ nparr
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR) # ทำการแปลง nparr ให้กลายเป็นภาพ
    return img # return รูปภาพ img 

def removehaze(img): # function สำหรับการลบหมอก โดยรับ img 
    original_height, original_width,_ = img.shape # ทำการอ่านรูปภาพเพื่อเอาค่า ความสูง และความกว้าง
    target_width = 320 # กำหนดความกว้างใหม่ของรูปภาพ
    target_height = 240 # กำหนดความสูงใหม่ของรูปภาพ
    small_HazeImg = cv2.resize(img, (target_width, target_height)) # ทำการปรับขนาดรูปภาพให้เป็นไปตามที่กำหนดไว้
    HazeImg, HazeMap = image_dehazer.remove_haze(small_HazeImg, showHazeTransmissionMap=False) # ทำการลบหมอกด้วย image_dehazer
    adjusted1 = cv2.convertScaleAbs(HazeImg,alpha =  1, beta= 20) # ปรับค่าสีให้กับรูปภาพที่ลบหมอกมาแล้ว
    base64 = frame_to_base64(adjusted1) # แปลง frame ของ adjusted1 ให้เป็น base64
    return base64 # return base64 รูปภาพที่ทำการลบหมอกและปรับแต่งแล้ว

def auto_cap(): # function auto_cap เป็น funtion สำหรับการทำงานเบื้องหลัง หรือการทำงานตามเวลาที่กำหนด
    global old_time # เรียกใช้ตัวแปร old_time จาก global
    live_data = live.get()
    streaming = "data:image/jpeg;base64,"+live_data
    img_ori = base64_to_img(live_data)
    removed=removehaze(img_ori) # ทำการลบหมอก
    current_timestamp = datetime.now() # ดึงเวลาปัจจุบันมาเก็บไว้ที่ current_timestamp
    if removed is not None: # ถ้า removed ไม่ใช่ค่า None ให้ทำตามเงื่อนไข
            if old_time == '' or old_time != current_timestamp:  # ถ้า old_time มีค่า None หรือ ไม่เท่ากับเวลาปัจจุบัน ให้ทำตามเงื่อนไข (มีไว้เพื่อป้องกันการทำซ้ำ)
                    data_to_add = {  # ข้อมูลที่ต้องการเพิ่มลงฐานข้อมูล
                    "img_original": streaming, # รูปภาพ base64 ต้นฉบับ
                    "img_removed": removed, # รูปภาพ base64 ที่ผ่านการลบหมอก
                    "log": { # หัวข้อ log
                        "date": current_timestamp, # เวลาปัจจุบัน
                    }
                }   
                    old_time = current_timestamp # เก็บ current_timestamp ไว้ใน old_time เพื่อใช้ในการเปรียบเทียบครั้งต่อไป
                    document_ref, _ = collection_ref.add(data_to_add) # ทำการบันทึกข้อมูลลงฐา่นข้อมูล
    return print("added streaming") # print add streaming 

def camera(): # function camera คือฟังก์ชั่นหลักของหน้า Streaming    
    st.session_state.running=True # กำหนดค่า sestion_state.running ให้เป็น None 
    
    #st.session_state.running=True # กำหนด sestion_state.running ให้เป็น True เพื่อเริ่มการทำงานของกล้องอัตโนมัติ
    st.set_page_config(layout="centered") # set หน้า page เป็นความ centered (จอแคบ)
    st.header(":rainbow[Welcome to Haze Removal Image Enchancement Perspective for IoT device]",) # แสดง header
    st.title("Streaming") # แสดง
    #cap = cv2.VideoCapture(ip_camera_url)  # อ่าน video จาก urlที่ได้
    image_slot = st.empty() # สร้างพื้นที่ empty สำหรับวางที่ streaming
    col = st.columns(3) # สร้าง column 3 ช่อง สำหรับเสร็จกึ่งกลางให้ปุ่ม
 
    with col[1]: # ช่องสอง
        capture_button = st.button('Capture Image',use_container_width=True) # สร้างปุ่มสำหรับบันทึกภาพจากกล้องถ่ายทอดสด

    while st.session_state.running==True: # ลูปที่ทำงานเมื่อ session_state.running มีค่าเท่ากับ True
        live_data = live.get()
        streaming = "data:image/jpeg;base64,"+live_data
        image_slot.image(streaming,use_column_width=True)
        if capture_button: # เมื่อมีการกดปุ่มบุนทึกภาพนิ่งจากกล้องถ่ายทอดสด ให้ทำตามเงื่อนไข
                img_ori = base64_to_img(live_data)
                removed=removehaze(img_ori) # ทำการลบหมอก
                col1, col2 = st.columns(2) #สร้าง column ขึ้นมา 2 ช่อง
                with col1: # เลือก col1
                    st.divider() # สร้างเส้นใต้
                     # ทำการแปลง frame ให้เป็น base64 
                    st.subheader("Before") # แสดง subheader
                    st.image(streaming, channels="BGR", use_column_width=True) # แสดงรูปต้นฉบับ 
                    st.image(image=base64_to_histogram(streaming),use_column_width=True) # แสดง histogram ของรูปภาพต้นฉบับ
                    
                with col2: # เลือก col2
                    st.divider() # สร้างเส้นใต้
                    st.subheader("After") # แสดง subheader 
                    st.image(removed, channels="BGR", use_column_width=True) # แสดงรูปหลังผ่านการลบหมอก
                    st.image(image=base64_to_histogram(removed),use_column_width=True) # แสดง histogram ของรูปภาพที่ผ่านการลบหมอก
                current_timestamp = datetime.now() # ดึงเวลาปัจจุบันเก็บไว้ที่ current_timestamp                     
                if removed is not None: # ถ้ามีการลบหมอกเกิดขึ้น จะทำตามเงื่อนไข
                    data_to_add = { # ข้อมูลที่ต้องการเพิ่มไปที่ฐานข้อมูล
                    "img_original": streaming, # รูปภาพต้นฉบับ
                    "img_removed": removed, # รูปภาพที่ผ่านการลบหมอก
                    "log": { # หัวข้อ log
                        "date": current_timestamp, # เวลาปัจจุบัน
                    }
        }
                document_ref, _ = collection_ref.add(data_to_add) # ทำการเพิ่มข้อมูลไปยังฐานข้อมูล
                capture_button=False
            
for hour in range(0, 24): # กำหนดขอบเขตการทำงานคือ 0 นาฬิกาถึง 24 นาฬิกา
    for minute in range(0, 60, 30): # กำหนดขอบเขตการทำงานของนาทีคือ เริ่มที่ 0 และสิ้นสุดที่ 60 นาที แล้วจะทำงานทุก ๆ 30 นาที
        scheduled_time = {'hour': str(hour).zfill(2), 'minute': str(minute).zfill(2)} # ทำการแปลง ชั่วโมงและนาที เป็นตัวเลข
        scheduler.add_job(auto_cap, trigger='cron', **scheduled_time) # กำหนดให้บันทึกรูปอัตโนมัติ ทุกๆ 30 นาที
           
scheduler.start() # เริ่มการทำงานในเบื้องหลัง
if __name__ == "__main__":
    camera() # เรียกใช้ function manual() 
