import streamlit as st
import pandas as pd
from datetime import datetime
from vnlunar import LunarDate
import gspread
from google.oauth2.service_account import Credentials

# Cấu hình trang
st.set_page_config(page_title="Lịch Gia Đình", page_icon="📅")

# Kết nối Google Sheets
def get_sheet():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets"]
        # Lấy thông tin từ secrets và ép kiểu dict
        creds_info = dict(st.secrets["gcp_service_account"])
        
        # XỬ LÝ LỖI PEM: Dọn dẹp các ký tự xuống dòng thừa
        if "private_key" in creds_info:
            creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n").strip()
            
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        client = gspread.authorize(creds)
        # Truy cập Sheet bằng ID
        return client.open_by_key(st.secrets["sheet_id"]).get_worksheet(0)
    except Exception as e:
        st.error(f"Lỗi kết nối Robot: {e}")
        return None

def get_lunar_now():
    now = datetime.now()
    lunar = LunarDate.from_solar_date(now.year, now.month, now.day)
    return f"{lunar.day}/{lunar.month}"

def check_password():
    if "password_correct" not in st.session_state:
        st.subheader("🔒 Đăng nhập")
        pw = st.text_input("Mật khẩu:", type="password")
        if st.button("Vào hệ thống"):
            if pw == st.secrets["password"]:
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("Sai mật khẩu!")
        return False
    return True

def main():
    st.title("📅 Quản Lý Sự Kiện Tự Động")
    sheet = get_sheet()
    if sheet is None: return

    # Hiển thị ngày hôm nay
    now = datetime.now()
    lunar_now = get_lunar_now()
    st.info(f"📅 Hôm nay: {now.strftime('%d/%m/%Y')} | 🌙 Âm lịch: {lunar_now}")

    # Thêm sự kiện
    with st.expander("➕ Thêm sự kiện mới", expanded=True):
        name = st.text_input("Tên sự kiện:")
        col1, col2 = st.columns(2)
        with col1:
            etype = st.radio("Loại:", ["Dương lịch", "Âm lịch"], horizontal=True)
        with col2:
            if etype == "Âm lịch":
                d = st.number_input("Ngày âm", 1, 30, 15)
                m = st.number_input("Tháng âm", 1, 12, 3)
                final_date = f"{int(d)}/{int(m)}"
            else:
                dt = st.date_input("Chọn ngày:", value=now)
                final_date = dt.strftime("%d/%m")

        if st.button("🚀 Lưu vĩnh viễn"):
            if name:
                sheet.append_row([name, final_date, etype])
                st.success("Đã lưu thành công!")
                st.rerun()

    # Hiển thị danh sách
    st.write("---")
    st.subheader("🔔 Danh sách đã lưu")
    try:
        data = sheet.get_all_records()
        if data:
            st.table(pd.DataFrame(data))
        else:
            st.write("Chưa có dữ liệu.")
    except:
        st.write("Đang tải dữ liệu...")

if check_password():
    main()
