import streamlit as st
import pandas as pd
from datetime import datetime
from vnlunar import LunarDate

# 1. Cấu hình
st.set_page_config(page_title="Nhắc Nhở Sự Kiện", page_icon="📅")

# Hàm đọc/ghi dữ liệu từ Google Sheets (dạng CSV export)
def load_data():
    sheet_id = st.secrets["sheet_id"]
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    try:
        return pd.read_csv(url)
    except:
        return pd.DataFrame(columns=["Tên", "Ngày", "Loại"])

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
    st.title("📅 Lịch Gia Đình Vĩnh Viễn")
    
    # Load dữ liệu từ Sheets
    df = load_data()

    with st.expander("➕ Thêm sự kiện mới"):
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

        if st.button("Lưu vĩnh viễn"):
            if name:
                st.warning("Anh hãy copy dòng này dán vào file Google Sheet của anh để lưu nhé (Tạm thời):")
                st.code(f"{name},{final_date},{etype}")
                # Lưu ý: Ghi trực tiếp vào Google Sheets từ Streamlit cần cài đặt Service Account phức tạp hơn.
                # Cách này giúp anh quản lý file Sheet thủ công nhưng cực kỳ an toàn.

    st.write("---")
    st.subheader("🔔 Danh sách sự kiện")
    st.table(df)

if check_password():
    main()
