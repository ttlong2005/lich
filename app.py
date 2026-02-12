import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import base64
import json

# --- CẤU HÌNH ---
st.set_page_config(page_title="Lịch Gia Đình", page_icon="📅")

def get_sheet():
    try:
        b64_str = st.secrets["google_key_base64"].strip().replace("\n", "").replace(" ", "")
        json_data = base64.b64decode(b64_str).decode('utf-8')
        creds_info = json.loads(json_data)
        if "private_key" in creds_info:
            creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        client = gspread.authorize(creds)
        return client.open_by_key(st.secrets["sheet_id"]).get_worksheet(0)
    except Exception as e:
        st.error(f"Lỗi kết nối Robot: {str(e)}")
        return None

def check_password():
    if "password_correct" not in st.session_state:
        st.subheader("🔒 Đăng nhập hệ thống")
        pw = st.text_input("Mật khẩu:", type="password")
        if st.button("Vào hệ thống"):
            if pw == st.secrets["password"]:
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("Sai mật khẩu!")
        return False
    return True

# --- GIAO DIỆN ---
if check_password():
    st.title("📅 Quản Lý Sự Kiện Gia Đình")
    sheet = get_sheet()
    
    if sheet:
        now = datetime.now()
        st.info(f"📅 Hôm nay: {now.strftime('%d/%m/%Y')}")

        with st.expander("➕ Thêm sự kiện mới", expanded=True):
            name = st.text_input("Tên sự kiện:")
            col1, col2 = st.columns(2)
            with col1:
                etype = st.radio("Loại ngày:", ["Dương lịch", "Âm lịch"], horizontal=True)
            with col2:
                if etype == "Âm lịch":
                    d = st.number_input("Ngày âm", 1, 30, 15)
                    m = st.number_input("Tháng âm", 1, 12, 1)
                    final_date = f"{int(d)}/{int(m)}"
                else:
                    dt = st.date_input("Chọn ngày:", value=now)
                    final_date = dt.strftime("%d/%m")

            if st.button("🚀 Lưu vào lịch"):
                if name:
                    sheet.append_row([name, final_date, etype])
                    st.success("Đã lưu!")
                    st.rerun()

        st.write("---")
        st.subheader("🔔 Danh sách sự kiện")
        try:
            data = sheet.get_all_records()
            if data:
                st.table(pd.DataFrame(data))
            else:
                st.write("Chưa có dữ liệu.")
        except:
            st.write("Đang tải dữ liệu...")
