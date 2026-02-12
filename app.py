import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Quản Lý Sự Kiện", page_icon="📅")

def get_sheet():
    try:
        # Đọc trực tiếp từ cấu hình service_account trong Secrets
        info = dict(st.secrets["service_account"])
        
        # Xử lý quan trọng: Biến chuỗi \n thành ký tự xuống dòng thực sự
        info["private_key"] = info["private_key"].replace("\\n", "\n")
        
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(info, scopes=scope)
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

if check_password():
    st.title("📅 Quản Lý Sự Kiện Gia Đình")
    sheet = get_sheet()
    
    if sheet:
        st.success("✅ Kết nối Google Sheets thành công!")
        # Hiển thị dữ liệu
        try:
            data = sheet.get_all_records()
            if data:
                st.dataframe(pd.DataFrame(data))
            else:
                st.info("Chưa có sự kiện nào trong danh sách.")
        except Exception as e:
            st.warning("Sheet trống hoặc chưa có tiêu đề (Tên, Ngày, Loại).")

        # Form thêm sự kiện đơn giản
        with st.expander("➕ Thêm sự kiện mới"):
            name = st.text_input("Tên sự kiện:")
            date = st.text_input("Ngày (VD: 15/01):")
            etype = st.selectbox("Loại:", ["Dương lịch", "Âm lịch"])
            if st.button("Lưu"):
                if name and date:
                    sheet.append_row([name, date, etype])
                    st.success("Đã thêm!")
                    st.rerun()
