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
import requests
import io
import image_dehazer

db = firestore.Client.from_service_account_json("$MY_SECRET_KEY") # เชื่อมต่อกับ ฐานข้อมูล firebase จากไฟล์ firestore-key.json
st.session_state.button = False # set state button ให้เป็น False เพื่อยกเลิก session สำหรับ ค้นหา ในหน้า Gallery

def base64_to_histogram(base64_image): # function ที่เปลี่ยนจาก base64 ให้เป็น histogram
    binary_image = base64.b64decode(base64_image) # ทำการแปลง base64 ให้เป็น binary
    image_np = np.frombuffer(binary_image, dtype=np.uint8) # สร้าง numpy array จาก buffer binary ด้วย unit8
    if len(image_np) != 320 * 240: # ถ้าขนาดรูป ไม่เท่ากับ 240*320 ให้ทำตามเงื่อนไข
        image_np = np.resize(image_np, (320, 240)) # แปลงขนาดรูปเป็น 240*320
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

def base64_encode_image(image_path):  # function สำหรับการเข้ารหัสรูปภาพให้้เป็น base64 ด้วยการรับ image_path
    with open(image_path, "rb") as image_file: # เปิดรูปภาพ image_path ในรูปแบบ rb
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8") #ทำการเข้ารหัสรูปภาพให้รูปภาพเปลี่ยนเป็น base64
    image = Image.open(io.BytesIO(base64.b64decode(encoded_string))) #เปลี่ยนรูปภาพจาก string ให้เป็น image
    target_width = 320 # กำหนดความกว้างของรูป
    target_height = 240 # กำหนดความสูงของรูป
    resized_image = image.resize((target_width, target_height)) # ปรับขนาดของรูปตามที่กำหนดไว้ในตัวแปร
    resized_binary = BytesIO() # สรา้ง object ขึ้นมาที่ resize_binary
    resized_image.save(resized_binary, format='PNG') # บันทึก object ลงไปที่ resizeg_image ด้วย format PNG
    resized_binary = base64.b64encode(resized_binary.getvalue()).decode("utf-8") # ถอดรหัสรูปภาพและเก็บค่าของรูปภาพไว้ที่ resized_binary ด้วย utf-8
    base64_original = resized_binary # เก็บค่าของ resized_binary ไว้ที่ base64_original
    return base64_original # return ค่า base64 กลับไป

def base64_format(base64): # function ที่แปลงข้อมูลให้เป็น base64 format
    base64_New = "data:image/jpeg;base64," + base64 # ใส่ baes64 format ลงไปในค่าที่รับมา
    return base64_New # return base64 ค่าใหม่กลับไป

def removehaze(img): # function สำหรับการลบหมอก โดยรับ img 
    original_height, original_width,_ = img.shape # ทำการอ่านรูปภาพเพื่อเอาค่า ความสูง และความกว้าง
    target_width = 320 # กำหนดความกว้างใหม่ของรูปภาพ
    target_height = 240 # กำหนดความสูงใหม่ของรูปภาพ
    small_HazeImg = cv2.resize(img, (target_width, target_height)) # ทำการปรับขนาดรูปภาพให้เป็นไปตามที่กำหนดไว้
    HazeImg, HazeMap = image_dehazer.remove_haze(small_HazeImg, showHazeTransmissionMap=False) # ทำการลบหมอกด้วย image_dehazer
    adjusted1 = cv2.convertScaleAbs(HazeImg,alpha =  1, beta= 20) # ปรับค่าสีให้กับรูปภาพที่ลบหมอกมาแล้ว
    base64 = frame_to_base64(adjusted1) # แปลง frame ของ adjusted1 ให้เป็น base64
    return base64 # return base64 รูปภาพที่ทำการลบหมอกและปรับแต่งแล้ว

def base64_to_img(base64_image): # function ในการทำ base64 เป็นรูปภาพด้วยการรับค่า base64
    image_data = base64.b64decode(base64_image) # ทำการถอดรหัส base64 ให้เป็นรูปภาพแล้วเก็บไว้ที่ image_data
    nparr = np.frombuffer(image_data, np.uint8) # นำ image_data มาใช้ numpy ในการสร้างภาพ และเก็บไว้ที่ nparr
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR) # ทำการแปลง nparr ให้กลายเป็นภาพ
    return img # return รูปภาพ img 

def frame_to_base64(frame): # function ในการแปลง frame ให้เป็น base64 โดยรับค่าจาก frame
    try: # ลอง
        frame_array = np.asarray(frame) # แปลง frame ที่รับมาให้เป็น array numpy แล้วเก็บไว้ที่ frame_array
        _, buffer = cv2.imencode('.jpg', frame_array) # ทำการแปลง frame ให้เป็นรูปภาพ นามสกุล .jpg ด้วย cv2 
        base64_data = base64.b64encode(buffer) # ทำการเข้ารหัส base64
        base64_string = base64_data.decode("utf-8")  # แปลงข้อมูล base64 ให้เป็น string ด้วย utf-8 แล้วเก็บไว้ที่ base64_string
        return base64_string # return ค่า base64 ที่เป็น string 
    except Exception as e: # หากพบปัญหา
            print(f"Error: {e}") # ให้ print ค่าทีี่ Error ออกมา
            return None # return ค่า None กลับไปหากมีปัญหา

def main(): # function main เป็นฟังก์ชั่นหลักในการทำงาน
    st.set_page_config(layout="centered") # set หน้า page เป็นความ centered (จอแคบ)
    st.header(":rainbow[Welcome to Haze Removal Image Enchancement Perspective for IoT device]",) # แสดง header
    collection_ref = db.collection("Images") # สร้างเส้นทางอ้างอิงไปยัง Images ในฐานข้อมูล
    uploaded_image = st.file_uploader("Choose an Image.") # สร้างที่ upload ไฟล์เก็บไว้ที่ uploaded_image
    document_ref = '' # สร้างตัวแปร document_ref เอาไว้
    if uploaded_image is not None: # ถ้ามีการอัปโหลดไฟล์ จะทำตามเงื่อนไข
        with tempfile.NamedTemporaryFile(delete=False) as temp_file: # สร้าง tempfile สำรหับจัดเก็บรูปขึ้นมา
            temp_file.write(uploaded_image.getvalue()) # นำค่าจากรูปที่อัปโหลดมาไว้ที่ temp_file
            file_path = temp_file.name # กำหนดให้ file_path = temp_file.name
            
        base64_original = base64_encode_image(file_path) # นำ file_path มาแปลงเป็นรูปและเก็บไว้
        base64_original_format = base64_format(base64_original) # นำมาแปลงเป็น format base64
        base_img = base64_to_img(base64_original) # แปลง base64 กลับไปเป็นรูปภาพ แล้วเก็บไว้ที่ base_img
        img_removed = removehaze(base_img) # นำ base_img มาทำการลบหมอก
        base64_removed = base64_format(img_removed) # นำรูปภาพที่ลบหมอกแล้วมาแปลงเป็น format base64
        current_timestamp = datetime.now() # ดึงเวลาปัจจุบันมาเก็บไว้ที่ current_timestamp
        if img_removed is not None: # ถ้ามีรูปลบหมอก ให้ทำตามเงื่อนไข
            data_to_add = { # ข้อมูลที่ต้องการจะเพิ่มลงฐานข้อมูล
                "img_original": base64_original_format, # รูปต้นฉบับก่อนลบหมอก
                "img_removed": base64_removed, # รูปหลังผ่านการลบหมอกแล้ว
                "log": { # หัวข้อ log
                    "date": current_timestamp, # เวลาปัจจุบันที่เก็บ วัน เดือน ปี / ชั่วโมง นาที วินาที เอาไว้
                }
            }
            document_ref, _ = collection_ref.add(data_to_add) # ทำการเพิ่มข้อมูลดังกล่าวไปยังฐานข้อมูล
            
        colu= st.columns(2) # สร้าง column 2 ช่องสำหรับนำผลลัพธ์มาแสดง
        with colu[0]: # เลือก colu ช่องแรก
            st.subheader("Before") # แสดง subheader
            st.image(base64_original_format, caption="Before Imaage",width=320) # แสดงรูปต้นฉบับ โดยมีความกว้าง 320
            st.image(base64_to_histogram(base64_original_format), caption="Before Imaage",width=320) # แสดงรูป histogram ของรูปต้นฉบับ โดยมีความกว้าง 320
        with colu[1]: # เลือก colu ช่องสอง
            st.subheader("After") # แสดง subheader   
            st.image(base64_removed, caption="After Image",width=320) #แสดงรูปที่ผ่านการลบหมอก โดยมีความกว้าง 320 
            st.image(base64_to_histogram(base64_removed), caption="After Image", width=320) # แสดงรูป histogram ของรูปที่ผ่านการลบหมอก โดยมีความกว้าง 320

if __name__ == "__main__":
    main() # เรียกใช้ function main() 
