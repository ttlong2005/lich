import streamlit as st
import pandas as pd
from datetime import datetime
from vnlunar import LunarDate

# Cấu hình giao diện
st.set_page_config(page_title="Nhắc Nhở Sự Kiện", page_icon="📅")

def get_lunar_info(solar_date):
    """Chuyển ngày dương sang ngày âm bằng thư viện vnlunar"""
    # Khởi tạo đối tượng LunarDate từ ngày dương lịch
    lunar = LunarDate.from_solar_date(solar_date.year, solar_date.month, solar_date.day)
    return f"{lunar.day}/{lunar.month}"

def main():
    st.title("📅 Quản Lý Sự Kiện Gia Đình")
    
    # Hiển thị ngày hôm nay song song Dương - Âm
    now = datetime.now()
    try:
        lunar_now = get_lunar_info(now)
        st.info(f"📅 Hôm nay: {now.strftime('%d/%m/%Y')} | 🌙 Âm lịch: {lunar_now}")
    except:
        st.info(f"📅 Hôm nay: {now.strftime('%d/%m/%Y')}")

    if 'events' not in st.session_state:
        st.session_state.events = []

    # --- PHẦN CHỌN LỊCH THÔNG MINH ---
    with st.expander("➕ Thêm sự kiện mới (Hiện cả âm và dương)", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Tên sự kiện (Ví dụ: Giỗ bà nội...)")
            event_type = st.radio("Loại lịch muốn lưu:", ["Dương lịch", "Âm lịch"], horizontal=True)
        
        with col2:
            # Khi anh chọn ngày ở đây, dòng chữ bên dưới sẽ báo ngay ngày âm tương ứng
            date_selected = st.date_input("Chọn ngày trên lịch:", value=now)
            
            try:
                lunar_val = get_lunar_info(date_selected)
                if event_type == "Âm lịch":
                    st.write(f"✨ Ngày âm tương ứng: **{lunar_val}**")
                else:
                    st.write(f"✨ Ngày dương đã chọn: **{date_selected.strftime('%d/%m')}**")
            except:
                lunar_val = "N/A"

        if st.button("🚀 Lưu vào danh sách"):
            if name:
                final_date = lunar_val if event_type == "Âm lịch" else date_selected.strftime("%d/%m")
                st.session_state.events.append({
                    "Tên sự kiện": name, 
                    "Ngày lưu": final_date, 
                    "Loại": event_type
                })
                st.rerun()
            else:
                st.error("Anh chưa nhập tên sự kiện!")

    # --- HIỂN THỊ DANH SÁCH ---
    st.write("---")
    st.subheader("🔔 Danh sách đã lưu")
    if st.session_state.events:
        df = pd.DataFrame(st.session_state.events)
        st.table(df)
        if st.button("🗑️ Xóa tất cả"):
            st.session_state.events = []
            st.rerun()
    else:
        st.write("Chưa có dữ liệu.")

if __name__ == "__main__":
    main()
