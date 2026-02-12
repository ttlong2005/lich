import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from vnlunar import LunarDate

# 1. Cấu hình trang
st.set_page_config(page_title="Lịch Gia Đình", page_icon="📅")

# 2. Kết nối Google Sheets (Cách mới đơn giản hơn)
def get_sheet_data():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # Đọc dữ liệu từ URL trong secrets
        df = conn.read(spreadsheet=st.secrets["spreadsheet"])
        return conn, df
    except Exception as e:
        st.error(f"Lỗi kết nối: {e}")
        return None, None

# 3. Hàm tính ngày âm lịch
def get_lunar_now():
    now = datetime.now()
    lunar = LunarDate.from_solar_date(now.year, now.month, now.day)
    return f"{lunar.day}/{lunar.month}"

# 4. Giao diện chính
st.title("📅 Quản Lý Sự Kiện Gia Đình")

conn, df = get_sheet_data()

if df is not None:
    now = datetime.now()
    st.info(f"📅 Hôm nay: {now.strftime('%d/%m/%Y')} | 🌙 Âm lịch: {get_lunar_now()}")

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
                # Tạo dòng mới
                new_row = pd.DataFrame([{"Tên sự kiện": name, "Ngày": final_date, "Loại": etype}])
                # Cập nhật vào Sheet
                updated_df = pd.concat([df, new_row], ignore_index=True)
                conn.update(spreadsheet=st.secrets["spreadsheet"], data=updated_df)
                st.success("Đã lưu thành công!")
                st.rerun()

    st.write("---")
    st.subheader("🔔 Danh sách sự kiện")
    st.table(df)
