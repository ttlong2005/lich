import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import requests

st.set_page_config(page_title="Quản Lý Sự Kiện", page_icon="📅")

# --- HÀM GỬI TELEGRAM (CÓ HIỂN THỊ LỖI ĐỂ KIỂM TRA) ---
def send_telegram(message):
    try:
        token = st.secrets["telegram_token"]
        chat_id = st.secrets["telegram_chat_id"]
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message}
        response = requests.post(url, data=payload)
        return response.json()
    except Exception as e:
        st.error(f"Lỗi gửi Telegram: {e}")
        return None

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

# --- GIAO DIỆN CHÍNH ---
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
        
        # --- NÚT BẤM TEST THỬ TELEGRAM NGAY LẬP TỨC ---
        if st.button("🚀 Bấm vào đây để Test gửi Telegram thử"):
            res = send_telegram("🔔 Tin nhắn thử nghiệm từ App Lịch Gia Đình! Nếu anh thấy tin này nghĩa là cấu hình đã ĐÚNG.")
            if res and res.get("ok"):
                st.success("✅ Telegram báo 'OK'! Anh kiểm tra điện thoại nhé.")
            else:
                st.error(f"❌ Telegram báo lỗi: {res}")

        st.write("---")
        
        # --- LOGIC THÔNG BÁO TỰ ĐỘNG ---
        now = datetime.now()
        upcoming_found = False
        
        for index, row in df.iterrows():
            try:
                # Ép kiểu ngày từ Sheet (giả sử là 27/12) thành ngày của năm hiện tại
                day, month = map(int, str(row['Ngày']).split('/'))
                event_date = datetime(now.year, month, day)
                
                # Tính khoảng cách
                diff = (event_date - now).days + 1
                
                # TEST: Nếu trong vòng 7 ngày tới thì thông báo luôn để anh dễ thấy
                if 0 <= diff <= 7:
                    msg = f"🔔 SẮP ĐẾN: '{row['Tên']}' còn {diff} ngày nữa là đến ({row['Ngày']})!"
                    send_telegram(msg)
                    st.info(f"📤 Đã tự động gửi thông báo cho: {row['Tên']}")
                    upcoming_found = True
            except:
                continue
        
        if not upcoming_found:
            st.write("Hiện tại không có sự kiện nào trong 7 ngày tới.")

        st.dataframe(df)

        with st.expander("➕ Thêm sự kiện mới"):
            name = st.text_input("Tên sự kiện:")
            date_input = st.text_input("Ngày (VD: 15/01):")
            etype = st.selectbox("Loại:", ["Dương lịch", "Âm lịch"])
            if st.button("Lưu"):
                if name and date_input:
                    sheet.append_row([name, date_input, etype])
                    st.success("Đã thêm thành công!")
                    st.rerun()
