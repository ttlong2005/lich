import streamlit as st
import pandas as pd
from vnlunar import LunarDate
import gspread
from google.oauth2.service_account import Credentials

def get_sheet():
    # Cách lấy thông tin Robot từ định dạng TOML của Streamlit
    creds_info = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_info)
    client = gspread.authorize(creds)
    return client.open_by_key(st.secrets["sheet_id"]).get_worksheet(0)

# ... (Các phần code main và login anh giữ nguyên như cũ) ...

st.set_page_config(page_title="Lịch Gia Đình Tự Động", page_icon="📅")

def check_password():
    if "password_correct" not in st.session_state:
        st.subheader("🔒 Đăng nhập hệ thống")
        pw = st.text_input("Mật khẩu:", type="password")
        if st.button("Vào app"):
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
    
    # --- PHẦN THÊM MỚI ---
    with st.expander("➕ Thêm sự kiện mới (Tự động lưu)", expanded=True):
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
                dt = st.date_input("Chọn ngày:")
                final_date = dt.strftime("%d/%m")

        if st.button("🚀 Lưu vĩnh viễn"):
            if name:
                # Robot tự động chèn thêm 1 dòng vào cuối Sheet
                sheet.append_row([name, final_date, etype])
                st.success(f"Đã lưu '{name}' vào Google Sheets!")
                st.rerun()

    # --- PHẦN HIỂN THỊ ---
    st.write("---")
    st.subheader("🔔 Danh sách từ Google Sheets")
    data = sheet.get_all_records()
    if data:
        df = pd.DataFrame(data)
        st.table(df)
    else:
        st.write("Chưa có dữ liệu.")

if check_password():
    main()
