import streamlit as st
import pandas as pd
from datetime import datetime
from vnlunar import LunarDate

st.set_page_config(page_title="Nhắc Nhở Sự Kiện", page_icon="📅")

def get_lunar_str(solar_date):
    """Trả về chuỗi ngày âm lịch từ ngày dương lịch"""
    lunar = LunarDate.from_solar_date(solar_date.year, solar_date.month, solar_date.day)
    return f"{lunar.day}/{lunar.month} (Âm lịch)"

def main():
    st.title("📅 Quản Lý Sự Kiện Gia Đình")
    
    # Hiển thị ngày hiện tại (Cả Dương và Âm)
    now = datetime.now()
    lunar_now = get_lunar_str(now)
    st.info(f"📅 Hôm nay: {now.strftime('%d/%m/%Y')} | 🌙 {lunar_now}")

    if 'events' not in st.session_state:
        st.session_state.events = []

    # --- PHẦN CHỌN LỊCH THÔNG MINH ---
    with st.expander("➕ Thêm sự kiện mới (Hỗ trợ tra lịch âm)", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Tên sự kiện (Ví dụ: Giỗ ông nội, Sinh nhật con...)")
            event_type = st.radio("Loại lịch muốn lưu:", ["Dương lịch", "Âm lịch"], horizontal=True)
        
        with col2:
            # Đây là phần anh cần: Chọn ngày dương để lấy ngày âm
            date_selected = st.date_input("Chọn một ngày bất kỳ để lấy mốc:")
            lunar_val = get_lunar_str(date_selected)
            
            if event_type == "Âm lịch":
                st.write(f"👉 Hệ thống sẽ lưu ngày: **{lunar_val}**")
            else:
                st.write(f"👉 Hệ thống sẽ lưu ngày: **{date_selected.strftime('%d/%m')} (Dương lịch)**")

        if st.button("🚀 Lưu vào danh sách"):
            if name:
                # Nếu là âm lịch thì lấy ngày/tháng của âm, ngược lại lấy dương
                lunar_obj = LunarDate.from_solar_date(date_selected.year, date_selected.month, date_selected.day)
                final_date = f"{lunar_obj.day}/{lunar_obj.month}" if event_type == "Âm lịch" else date_selected.strftime("%d/%m")
                
                st.session_state.events.append({
                    "Tên": name, 
                    "Ngày lưu": final_date, 
                    "Loại": event_type,
                    "Ghi chú": f"Gốc từ ngày {date_selected.strftime('%d/%m/%Y')}"
                })
                st.success("Đã thêm thành công!")
                st.rerun()
            else:
                st.warning("Anh quên nhập tên sự kiện kìa!")

    # --- HIỂN THỊ ---
    st.write("---")
    st.subheader("🔔 Danh sách nhắc hẹn")
    if st.session_state.events:
        df = pd.DataFrame(st.session_state.events)
        st.dataframe(df, use_container_width=True)
        if st.button("🗑️ Xóa sạch danh sách"):
            st.session_state.events = []
            st.rerun()
    else:
        st.write("Chưa có dữ liệu nào được lưu.")

if __name__ == "__main__":
    main()
