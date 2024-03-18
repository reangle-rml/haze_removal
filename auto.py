import firebase_admin
from firebase_admin import credentials,db ,initialize_app
import schedule
from google.cloud import firestore
import time
from datetime import datetime
import base64
import numpy as np
import cv2
import image_dehazer
from io import BytesIO

try:
    # ลองดึง Firebase app ที่ถูก initialize
    app = firebase_admin.get_app()
    print("Firebase app is already initialized.")
except ValueError:
    cred = credentials.Certificate("firestore_key.json") # ยืนยันตัวตน firebase จากไฟล์ firestore-key.json
    initialize_app(cred, {"databaseURL": "https://haze-remover-default-rtdb.asia-southeast1.firebasedatabase.app/"})
    print("Firebase app initialized.")
dab = firestore.Client.from_service_account_json("firestore_key.json") # เชื่อมต่อกับ ฐานข้อมูล firebase จากไฟล์ firestore-key.json 

# กำหนดเวลาเริ่มต้นและสิ้นสุดที่ต้องการ
start_time = datetime.strptime("06:00:00", "%H:%M:%S")
end_time = datetime.strptime("17:00:00", "%H:%M:%S")
collection_ref = dab.collection("Images_camera") # สร้างเส้นทางอ้างอิงไปยัง Images ในฐานข้อมูล
live = db.reference("image_original") # สร้างเส้นทางอ้างอิงไปยัง image_original ไปยัง realtime database

# เชื่อมต่อกับ Firestore

def frame_to_base64(frame):
    _, buffer = cv2.imencode(".jpeg", frame)  # ทำการแปลง frame ให้เป็นรูปภาพ นามสกุล .jpeg ด้วย cv2 
    frame_bytes = BytesIO(buffer.tobytes()) # สร้าง Object จาก buffer แล้วเป็น bytes แล้วเก็บไว้ที่ frame_bytes
    encoded_string = base64.b64encode(frame_bytes.read()).decode("utf-8") # ทำการถอดรหัส frame ให้เป็น base64
    return "data:image/jpeg;base64," + encoded_string # return ค่า base64 ที่ทำการใส่ format base64 เข้าไป


def removehaze(img): # function สำหรับการลบหมอก โดยรับ img 
    original_height, original_width,_ = img.shape # ทำการอ่านรูปภาพเพื่อเอาค่า ความสูง และความกว้าง
    target_width = 320 # กำหนดความกว้างใหม่ของรูปภาพ
    target_height = 240 # กำหนดความสูงใหม่ของรูปภาพ
    small_HazeImg = cv2.resize(img, (target_width, target_height)) # ทำการปรับขนาดรูปภาพให้เป็นไปตามที่กำหนดไว้
    HazeImg, HazeMap = image_dehazer.remove_haze(small_HazeImg, showHazeTransmissionMap=False) # ทำการลบหมอกด้วย image_dehazer
    adjusted1 = cv2.convertScaleAbs(HazeImg,alpha =  1, beta= 20) # ปรับค่าสีให้กับรูปภาพที่ลบหมอกมาแล้ว
    base64 = frame_to_base64(adjusted1) # แปลง frame ของ adjusted1 ให้เป็น base64
    return base64 # return base64 รูปภาพที่ทำการลบหมอกและปรับแต่งแล้ว

def upload_data_to_firestore():
    # ใส่โค้ดที่ต้องการอัปโหลดข้อมูลไปยัง Firestore ที่นี่
    print("Gonna add")
    db.collection("Test").add({"key": "value"})
    print("Uploaded data to Firestore at", datetime.now())

# สร้างตัวตรวจสอบเวลาและทำงาน
def check_and_upload():
    current_time = datetime.now().time()
    if start_time.time() <= current_time <= end_time.time():
        auto_cap()
    print(current_time)
    print(start_time.time())
    print(end_time.time())

def base64_to_img(base64_image): # function ในการทำ base64 เป็นรูปภาพด้วยการรับค่า base64
    image_data = base64.b64decode(base64_image) # ทำการถอดรหัส base64 ให้เป็นรูปภาพแล้วเก็บไว้ที่ image_data
    nparr = np.frombuffer(image_data, np.uint8) # นำ image_data มาใช้ numpy ในการสร้างภาพ และเก็บไว้ที่ nparr
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR) # ทำการแปลง nparr ให้กลายเป็นภาพ
    return img # return รูปภาพ img 


def auto_cap(): # function auto_cap เป็น funtion สำหรับการทำงานเบื้องหลัง หรือการทำงานตามเวลาที่กำหนด
    live_data = live.get()
    streaming = "data:image/jpeg;base64,"+live_data
    img_ori = base64_to_img(live_data)
    removed=removehaze(img_ori) # ทำการลบหมอก
    current_timestamp = datetime.now() # ดึงเวลาปัจจุบันมาเก็บไว้ที่ current_timestamp
    if removed is not None: # ถ้า removed ไม่ใช่ค่า None ให้ทำตามเงื่อนไข
                    data_to_add = {  # ข้อมูลที่ต้องการเพิ่มลงฐานข้อมูล
                    "img_original": streaming, # รูปภาพ base64 ต้นฉบับ
                    "img_removed": removed, # รูปภาพ base64 ที่ผ่านการลบหมอก
                    "log": { # หัวข้อ log
                        "date": current_timestamp, # เวลาปัจจุบัน
                    }
                }   
                    document_ref, _ = collection_ref.add(data_to_add) # ทำการบันทึกข้อมูลลงฐา่นข้อมูล
    return print("Auto Capture!") # print add streaming 

# ตั้งค่าตารางเวลาให้ทำงานทุกๆ 30 นาที
schedule.every(30).minutes.do(check_and_upload)

# ลูปเพื่อตรวจสอบตารางเวลาและทำงาน
while True:
    schedule.run_pending()
    time.sleep(1)
