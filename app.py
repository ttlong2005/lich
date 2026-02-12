import streamlit as st
import pandas as pd
from datetime import datetime
from vietnamselunarcalendar import LunarDate

# Cấu hình giao diện
st.set_page_config(page_title="Nhắc Nhở Sự Kiện", page_icon="📅")

def get_lunar_info(solar_date):
    """Chuyển ngày dương sang chuỗi ngày âm"""
    lunar = LunarDate.from_solar_date(solar_date.year, solar_date.month, solar_date.day)
    return f"{lunar.day}/{lunar.month}"

def main():
    st.title("📅 Quản Lý Sự Kiện Gia Đình")
    
    # Hiển thị ngày hôm nay song song
    now = datetime.now()
    lunar_now = get_lunar_info(now)
    st.info(f"📅 Hôm nay: {now.strftime('%d/%m/%Y')} | 🌙 Âm lịch: {lunar_now}")

    if 'events' not in st.session_state:
        st.session_state.events = []

    # --- PHẦN CHỌN LỊCH THÔNG MINH ---
    with st.expander("➕ Thêm sự kiện mới (Hỗ trợ tra lịch âm)", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Tên sự kiện (Ví dụ: Đám giỗ cụ...)")
            event_type = st.radio("Loại lịch muốn lưu:", ["Dương lịch", "Âm lịch"], horizontal=True)
        
        with col2:
            # Chọn ngày dương lịch để ứng dụng tự tính ngày âm
            date_selected = st.date_input("Chọn ngày trên lịch:")
            lunar_val = get_lunar_info(date_selected)
            
            if event_type == "Âm lịch":
                st.write(f"✨ Ngày âm tương ứng: **{lunar_val}**")
                st.caption("(Ứng dụng sẽ tự động nhắc vào ngày này hàng năm)")
            else:
                st.write(f"✨ Ngày dương đã chọn: **{date_selected.strftime('%d/%m')}**")

        if st.button("🚀 Lưu sự kiện"):
            if name:
                # Quyết định lưu theo ngày âm hay dương
                final_date = lunar_val if event_type == "Âm lịch" else date_selected.strftime("%d/%m")
                
                st.session_state.events.append({
                    "Tên sự kiện": name, 
                    "Ngày lưu": final_date, 
                    "Loại lịch": event_type
                })
                st.success(f"Đã thêm: {name}")
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
        st.write("Chưa có sự kiện nào.")

if __name__ == "__main__":
    main()
