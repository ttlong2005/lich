import streamlit as st
import pandas as pd
from datetime import datetime
from vnlunar import LunarDate

# Cấu hình giao diện
st.set_page_config(page_title="Nhắc Nhở Sự Kiện", page_icon="📅")

def get_lunar_now():
    """Lấy ngày âm lịch hiện tại"""
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

    # --- PHẦN NHẬP LIỆU THÔNG MINH ---
    with st.expander("➕ Thêm sự kiện mới", expanded=True):
        name = st.text_input("Tên sự kiện (Ví dụ: Giỗ bà nội, Sinh nhật...)")
        
        col1, col2 = st.columns(2)
        with col1:
            event_type = st.radio("Loại lịch muốn lưu:", ["Dương lịch", "Âm lịch"], horizontal=True)
        
        with col2:
            if event_type == "Âm lịch":
                # Nếu chọn âm lịch, cho phép chọn trực tiếp Ngày và Tháng âm
                sub_col1, sub_col2 = st.columns(2)
                with sub_col1:
                    lunar_day = st.number_input("Ngày âm", min_value=1, max_value=30, value=15)
                with sub_col2:
                    lunar_month = st.number_input("Tháng âm", min_value=1, max_value=12, value=3)
                final_date = f"{int(lunar_day)}/{int(lunar_month)}"
                st.write(f"👉 Sẽ nhắc vào ngày **{final_date} Âm lịch** hàng năm.")
            else:
                # Nếu chọn dương lịch, hiện ô chọn lịch như bình thường
                date_selected = st.date_input("Chọn ngày dương trên lịch:", value=now)
                final_date = date_selected.strftime("%d/%m")
                st.write(f"👉 Sẽ nhắc vào ngày **{final_date} Dương lịch** hàng năm.")

        if st.button("🚀 Lưu vào danh sách"):
            if name:
                st.session_state.events.append({
                    "Tên sự kiện": name, 
                    "Ngày lưu": final_date, 
                    "Loại": event_type
                })
                st.success(f"Đã thêm thành công: {name}")
                st.rerun()
            else:
                st.error("Anh chưa nhập tên sự kiện kìa!")

    # --- HIỂN THỊ DANH SÁCH ---
    st.write("---")
    st.subheader("🔔 Danh sách đã lưu")
    if st.session_state.events:
        df = pd.DataFrame(st.session_state.events)
        # Hiển thị bảng đẹp hơn
        st.table(df)
        
        if st.button("🗑️ Xóa sạch danh sách"):
            st.session_state.events = []
            st.rerun()
    else:
        st.write("Chưa có dữ liệu nào được lưu.")

if __name__ == "__main__":
    main()
