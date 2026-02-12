import streamlit as st
import pandas as pd
from datetime import datetime
from vnlunar import LunarDate
import gspread
from google.oauth2.service_account import Credentials

# 1. Cấu hình trang
st.set_page_config(page_title="Lịch Gia Đình", page_icon="📅")

# 2. Hàm kết nối Google Sheets (Đã xử lý lỗi InvalidByte)
def get_sheet():
    try:
        # Lấy thông tin từ Secrets
        creds_info = dict(st.secrets["gcp_service_account"])
        
        # Làm sạch mã khóa để tránh lỗi ký tự lạ (InvalidByte)
        if "private_key" in creds_info:
            creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n").strip()
            
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        client = gspread.authorize(creds)
        
        # Mở Sheet bằng ID (Lấy từ Secrets)
        return client.open_by_key(st.secrets["sheet_id"]).get_worksheet(0)
    except Exception as e:
        st.error(f"Lỗi kết nối Robot: {str(e)}")
        return None

# 3. Hàm tính ngày âm lịch
def get_lunar_now():
    now = datetime.now()
    lunar = LunarDate.from_solar_date(now.year, now.month, now.day)
    return f"{lunar.day}/{lunar.month}"

# 4. Kiểm tra mật khẩu
def check_password():
    if "password_correct" not in st.session_state:
        st.subheader("🔒 Đăng nhập hệ thống")
        pw = st.text_input("Nhập mật khẩu:", type="password")
        if st.button("Vào hệ thống"):
            if pw == st.secrets["password"]:
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("Sai mật khẩu rồi anh ơi!")
        return False
    return True

# 5. Giao diện chính
def main():
    st.title("📅 Quản Lý Sự Kiện Gia Đình")
    
    sheet = get_sheet()
    if sheet is None:
        return

    # Hiển thị ngày tháng hiện tại
    now = datetime.now()
    lunar_now = get_lunar_now()
    st.info(f"📅 Hôm nay: {now.strftime('%d/%m/%Y')} | 🌙 Âm lịch: {lunar_now}")

    # Phần thêm sự kiện
    with st.expander("➕ Thêm sự kiện mới", expanded=True):
        name = st.text_input("Tên sự kiện (VD: Giỗ ông nội, Sinh nhật con...):")
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
                try:
                    sheet.append_row([name, final_date, etype])
                    st.success("Đã lưu thành công vào Google Sheet!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi khi lưu dữ liệu: {e}")
            else:
                st.warning("Anh quên chưa nhập tên sự kiện rồi!")

    # Hiển thị danh sách từ Google Sheets
    st.write("---")
    st.subheader("🔔 Danh sách sự kiện đã lưu")
    try:
        data = sheet.get_all_records()
        if data:
            df = pd.DataFrame(data)
            st.table(df)
        else:
            st.write("Hiện chưa có sự kiện nào được lưu.")
    except Exception as e:
        st.write("Đang tải dữ liệu...")

# Chạy ứng dụng
if check_password():
    main()
