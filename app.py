import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import requests
from lunarcalendar import Lunar, Converter

st.set_page_config(page_title="Quản Lý Sự Kiện Gia Đình", page_icon="📅")

# --- HÀM CHUYỂN ÂM SANG DƯƠNG ---
def get_solar_from_lunar(lunar_day, lunar_month):
    try:
        now = datetime.now()
        lunar_date = Lunar(now.year, lunar_month, lunar_day)
        solar_date = Converter.LunarToSolar(lunar_date)
        dt_solar = datetime(solar_date.year, solar_date.month, solar_date.day)
        
        if (dt_solar.date() - now.date()).days < 0:
            lunar_date = Lunar(now.year + 1, lunar_month, lunar_day)
            solar_date = Converter.LunarToSolar(lunar_date)
            dt_solar = datetime(solar_date.year, solar_date.month, solar_date.day)
        return dt_solar
    except:
        return None

def send_telegram(message):
    try:
        token = st.secrets["telegram_token"]
        chat_id = st.secrets["telegram_chat_id"]
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"})
    except: pass

def get_sheet():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n")
        creds = Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds).open_by_key(st.secrets["sheet_id"]).get_worksheet(0)
    except: return None

if "password_correct" not in st.session_state:
    st.subheader("🔒 Đăng nhập")
    pw = st.text_input("Mật khẩu:", type="password")
    if st.button("Vào hệ thống"):
        if pw == st.secrets["password"]:
            st.session_state.password_correct = True
            st.rerun()
else:
    st.title("📅 Quản Lý Sự Kiện Gia Đình")
    sheet = get_sheet()
    if sheet:
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        now = datetime.now()
        days_left_list = []

        for index, row in df.iterrows():
            try:
                day, month = map(int, str(row['Ngày']).split('/'))
                if "Âm lịch" in str(row['Loại']):
                    event_date = get_solar_from_lunar(day, month)
                else:
                    event_date = datetime(now.year, month, day)
                    if (event_date.date() - now.date()).days < 0:
                        event_date = datetime(now.year + 1, month, day)
                
                if event_date:
                    diff = (event_date.date() - now.date()).days
                    days_left_list.append(diff)
                    if diff == 3:
                        send_telegram(f"🔔 *NHẮC NHỞ:* {row['Tên']} ({row['Ngày']}) còn 3 ngày nữa!")
                else:
                    days_left_list.append(999) # Giá trị tạm nếu lỗi
            except:
                days_left_list.append(999)

        df['Số ngày sắp đến'] = days_left_list
        # Sắp xếp để những ngày gần nhất (số nhỏ) hiện lên đầu
        df_sorted = df.sort_values(by='Số ngày sắp đến')
        st.dataframe(df_sorted, width='stretch')
