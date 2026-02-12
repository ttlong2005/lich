import streamlit as st
import pandas as pd
from datetime import datetime
from vnlunar import LunarDate

st.set_page_config(page_title="Nhắc Nhở Sự Kiện", page_icon="📅")

def get_lunar_date(solar_date):
    # Chuyển đổi sang âm lịch dùng vnlunar
    lunar = LunarDate.from_solar_date(solar_date.year, solar_date.month, solar_date.day)
    return f"{lunar.day}/{lunar.month}"

def main():
    st.title("📅 Quản Lý Sự Kiện Gia Đình")
    
    # Hiển thị ngày tháng hiện tại
    now = datetime.now()
    lunar_now = get_lunar_date(now)
    st.info(f"Hôm nay: {now.strftime('%d/%m/%Y')} (Âm lịch: {lunar_now})")

    if 'events' not in st.session_state:
        st.session_state.events = [
            {"Tên": "Kỷ niệm ngày cưới", "Ngày": "20/10", "Loại": "Dương lịch"},
            {"Tên": "Giỗ Cụ Nội", "Ngày": "15/03", "Loại": "Âm lịch"}
        ]

    with st.expander("➕ Thêm sự kiện mới"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Tên sự kiện")
            event_type = st.selectbox("Loại lịch", ["Dương lịch", "Âm lịch"])
        with col2:
            date_selected = st.date_input("Chọn ngày")
            
        if st.button("Lưu sự kiện"):
            day_month = date_selected.strftime("%d/%m")
            st.session_state.events.append({"Tên": name, "Ngày": day_month, "Loại": event_type})
            st.rerun()

    st.write("---")
    st.subheader("🔔 Các sự kiện đã lưu")
    if st.session_state.events:
        df = pd.DataFrame(st.session_state.events)
        st.table(df)
        if st.button("Xóa tất cả"):
            st.session_state.events = []
            st.rerun()

if __name__ == "__main__":
    main()
