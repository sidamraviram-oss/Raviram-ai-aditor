from fastapi import FastAPI, UploadFile, File, Form, Response, Query
import shutil
import os
import qrcode
import io
import base64
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = FastAPI(title="Raviram Secure AI Video & Audio Editor")

UPLOAD_DIR = "uploads"
AUDIO_DIR = "audio_uploads"
VIDEO_DIR = "video_uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

ADMIN_SECRET_KEY = "raviram0536"
SECURE_PHONE_NUMBER = "9502981109"
SECURE_UPI_ID = f"{SECURE_PHONE_NUMBER}@paytm"
OWNER_NAME = "Raviram"

def save_to_google_sheet(data_dict):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("google_credentials.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open("AI_Video_Generator_Logs").sheet1
        
        row_values = [
            data_dict.get("timestamp"),
            data_dict.get("role"),
            data_dict.get("project_type"),
            data_dict.get("uploaded_image"),
            data_dict.get("uploaded_audio"),
            data_dict.get("uploaded_video"),
            data_dict.get("bg_effect"),
            data_dict.get("lighting_effect"),
            data_dict.get("voice_effect"),
            str(data_dict.get("video_duration_minutes")),
            str(data_dict.get("total_amount")),
            str(data_dict.get("status"))
        ]
        sheet.append_row(row_values)
    except Exception as e:
        print("Google Sheet Error:", str(e))

def calculate_amount(minutes: int) -> float:
    if minutes <= 1:
        return 59.0
    elif minutes <= 3:
        return 149.0
    elif minutes <= 5:
        return 299.0
    elif minutes <= 10:
        return 599.0
    else:
        return float(minutes * 60)

@app.get("/")
async def home_page():
    return {
        "welcome": "Welcome to Raviram Secure AI Video & Audio Editor!",
        "pricing_list": [
            {"duration": "1 Minute", "price": "₹59"},
            {"duration": "3 Minutes", "price": "₹149"},
            {"duration": "5 Minutes", "price": "₹299"},
            {"duration": "10 Minutes", "price": "₹599"}
        ]
    }

@app.post("/edit-and-generate-video/")
async def edit_and_generate_video(
    project_type: str = Form("Short Film"),                          
    file: UploadFile = File(None),                                   
    audio_file: UploadFile = File(None),                           
    raw_video: UploadFile = File(None),                            
    bg_effect: str = Form("Cinematic Background"),                   
    lighting_effect: str = Form("Dramatic Lighting"),                
    voice_effect: str = Form("Studio Quality Voice"),                
    video_minutes: int = Form(3),                                    
    secret_key: str = Form(None)                                     
):
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        image_name = file.filename if file else "No Image"
        if file:
            with open(os.path.join(UPLOAD_DIR, file.filename), "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

        audio_name = audio_file.filename if audio_file else "No Audio"
        if audio_file:
            with open(os.path.join(AUDIO_DIR, audio_name), "wb") as buffer:
                shutil.copyfileobj(audio_file.file, buffer)

        video_name = raw_video.filename if raw_video else "No Video"
        if raw_video:
            with open(os.path.join(VIDEO_DIR, video_name), "wb") as buffer:
                shutil.copyfileobj(raw_video.file, buffer)

        amount = calculate_amount(video_minutes)

        if secret_key == ADMIN_SECRET_KEY:
            role = "Boss (Raviram)"
            status = "Success (Free Access)"
            
            log_data = {
                "timestamp": current_time, "role": role, "project_type": project_type,
                "uploaded_image": image_name, "uploaded_audio": audio_name, "uploaded_video": video_name,
                "bg_effect": bg_effect, "lighting_effect": lighting_effect, "voice_effect": voice_effect,
                "video_duration_minutes": video_minutes, "total_amount": 0.0, "status": status
            }
            save_to_google_sheet(log_data)

            return {
                "status": "Success",
                "role": role,
                "message": "Welcome Boss Raviram! Free access granted securely.",
                "payment_required": False,
                "final_edited_video": "https://ai-video-generator.local/raviram_secure_output.mp4"
            }

        upi_pay_link = f"upi://pay?pa={SECURE_UPI_ID}&pn={OWNER_NAME}&am={amount}&cu=INR"
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(upi_pay_link)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        qr_base64 = base64.b64encode(img_byte_arr.getvalue()).decode("utf-8")
        qr_image_data_url = f"data:image/png;base64,{qr_base64}"
        
        status = "Payment Required"
        role = "Regular User"

        log_data = {
            "timestamp": current_time, "role": role, "project_type": project_type,
            "uploaded_image": image_name, "uploaded_audio": audio_name, "uploaded_video": video_name,
            "bg_effect": bg_effect, "lighting_effect": lighting_effect, "voice_effect": voice_effect,
            "video_duration_minutes": video_minutes, "total_amount": amount, "status": status
        }
        save_to_google_sheet(log_data)

        return {
            "status": status,
            "role": role,
            "message": f"Please pay ₹{amount} to process your video.",
            "payment_required": True,
            "payment_details": {
                "total_amount": amount,
                "upi_intent_link": upi_pay_link,
                "qr_code_scanner": qr_image_data_url
            },
            "final_edited_video": None
        }

    except Exception as e:
        return {"status": "Error", "message": str(e)}
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi import Depends, HTTPException, status

security = HTTPBasic()

# ఇక్కడ మీకు నచ్చిన యూజర్ నేమ్ మరియు పాస్‌వర్డ్ పెట్టుకోండి
ADMIN_USER = "admin"
ADMIN_PASS = "raviram0536"

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != ADMIN_USER or credentials.password != ADMIN_PASS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
