import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials
import requests

st.set_page_config(page_title="Quản Lý Sự Kiện", page_icon="📅")

# Hàm gửi tin nhắn Telegram
def send_telegram(message):
    token = st.secrets["telegram_token"]
    chat_id = st.secrets["telegram_chat_id"]
    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}"
    try:
        requests.get(url)
    except:
        pass

def get_sheet():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n")
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(info, scopes=scope)
        client = gspread.authorize(creds)
        return client.open_by_key(st.secrets["sheet_id"]).get_worksheet(0)
    except Exception as e:
        st.error(f"Lỗi kết nối Robot: {str(e)}")
        return None

if "password_correct" not in st.session_state:
    st.subheader("🔒 Đăng nhập hệ thống")
    pw = st.text_input("Mật khẩu:", type="password")
    if st.button("Vào hệ thống"):
        if pw == st.secrets["password"]:
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("Sai mật khẩu!")
else:
    st.title("📅 Quản Lý Sự Kiện Gia Đình")
    sheet = get_sheet()
    
    if sheet:
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        # --- LOGIC KIỂM TRA VÀ GỬI THÔNG BÁO ---
        now = datetime.now()
        for index, row in df.iterrows():
            try:
                # Giả định định dạng ngày trong sheet là DD/MM
                event_date_str = row['Ngày'] + f"/{now.year}"
                event_date = datetime.strptime(event_date_str, "%d/%m/%Y")
                
                # Tính khoảng cách ngày
                diff = (event_date - now).days + 1
                
                # Nếu cách đúng 3 ngày thì gửi thông báo
                if diff == 3:
                    msg = f"🔔 THÔNG BÁO: Sự kiện '{row['Tên']}' sẽ diễn ra sau 3 ngày nữa ({row['Ngày']})!"
                    send_telegram(msg)
                    st.info(f"🚀 Đã gửi thông báo Telegram cho sự kiện: {row['Tên']}")
            except:
                continue
        
        st.success("✅ Đã kiểm tra lịch và gửi thông báo nếu có sự kiện sắp tới.")
        st.dataframe(df)

        with st.expander("➕ Thêm sự kiện mới"):
            name = st.text_input("Tên sự kiện:")
            date = st.text_input("Ngày (VD: 15/01):")
            etype = st.selectbox("Loại:", ["Dương lịch", "Âm lịch"])
            if st.button("Lưu"):
                if name and date:
                    sheet.append_row([name, date, etype])
                    st.success("Đã thêm!")
                    st.rerun()
