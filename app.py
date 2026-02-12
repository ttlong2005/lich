import streamlit as st
import pandas as pd
from datetime import datetime
from vnlunar import LunarDate

# 1. Cấu hình giao diện
st.set_page_config(page_title="Nhắc Nhở Sự Kiện", page_icon="📅")

# 2. Hàm kiểm tra đăng nhập
def check_password():
    """Trả về True nếu người dùng nhập đúng mật khẩu."""
    if "password_correct" not in st.session_state:
        st.subheader("🔒 Đăng nhập để sử dụng")
        password_input = st.text_input("Nhập mật khẩu của anh:", type="password")
        if st.button("Đăng nhập"):
            # Kiểm tra mật khẩu từ mục Secrets đã thiết lập ở Bước 1
            if password_input == st.secrets["password"]:
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("❌ Mật khẩu sai rồi anh ơi!")
        return False
    return True

def get_lunar_now():
    now = datetime.now()
    lunar = LunarDate.from_solar_date(now.year, now.month, now.day)
    return f"{lunar.day}/{lunar.month}"

def main():
    st.title("📅 Quản Lý Sự Kiện Gia Đình")
    
    # Hiển thị ngày hôm nay
    now = datetime.now()
    try:
        lunar_now = get_lunar_now()
        st.info(f"📅 Hôm nay: {now.strftime('%d/%m/%Y')} | 🌙 Âm lịch: {lunar_now}")
    except:
        st.info(f"📅 Hôm nay: {now.strftime('%d/%m/%Y')}")

    if 'events' not in st.session_state:
        st.session_state.events = []

    # --- PHẦN NHẬP LIỆU ---
    with st.expander("➕ Thêm sự kiện mới", expanded=True):
        name = st.text_input("Tên sự kiện:")
        col1, col2 = st.columns(2)
        with col1:
            event_type = st.radio("Loại lịch:", ["Dương lịch", "Âm lịch"], horizontal=True)
        with col2:
            if event_type == "Âm lịch":
                c1, c2 = st.columns(2)
                lunar_day = c1.number_input("Ngày âm", 1, 30, 15)
                lunar_month = c2.number_input("Tháng âm", 1, 12, 3)
                final_date = f"{int(lunar_day)}/{int(lunar_month)}"
            else:
                date_selected = st.date_input("Chọn ngày dương:", value=now)
                final_date = date_selected.strftime("%d/%m")

        if st.button("🚀 Lưu sự kiện"):
            if name:
                st.session_state.events.append({"Tên": name, "Ngày": final_date, "Loại": event_type})
                st.success("Đã lưu!")
                st.rerun()

    # --- HIỂN THỊ ---
    st.write("---")
    st.subheader("🔔 Danh sách đã lưu")
    if st.session_state.events:
        df = pd.DataFrame(st.session_state.events)
        st.table(df)
        if st.button("🗑️ Xóa sạch danh sách"):
            st.session_state.events = []
            st.rerun()
    
    # Nút đăng xuất
    if st.sidebar.button("Đăng xuất"):
        del st.session_state.password_correct
        st.rerun()

# Chạy chương trình
if check_password():
    main()
