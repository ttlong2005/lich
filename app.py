import streamlit as st
import pandas as pd
from datetime import datetime
from vietnam_pro_calendar import Calendar

# Cấu hình trang
st.set_page_config(page_title="Nhắc Nhở Sự Kiện", page_icon="📅")

def get_lunar_date(solar_date):
    """Chuyển đổi ngày dương sang âm lịch"""
    cal = Calendar()
    lunar = cal.solar_to_lunar(solar_date.day, solar_date.month, solar_date.year)
    return f"{lunar[0]}/{lunar[1]}"

def main():
    st.title("📅 Quản Lý Sự Kiện Gia Đình")
    st.subheader(f"Hôm nay: {datetime.now().strftime('%d/%m/%Y')}")

    # Khởi tạo dữ liệu mẫu trong session_state
    if 'events' not in st.session_state:
        st.session_state.events = [
            {"Tên": "Kỷ niệm ngày cưới", "Ngày": "20/10", "Loại": "Dương lịch"},
            {"Tên": "Giỗ Cụ Nội", "Ngày": "15/03", "Loại": "Âm lịch"}
        ]

    # --- PHẦN 1: THÊM SỰ KIỆN MỚI ---
    with st.expander("➕ Thêm sự kiện mới"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Tên sự kiện")
            event_type = st.selectbox("Loại lịch", ["Dương lịch", "Âm lịch"])
        with col2:
            date_selected = st.date_input("Chọn ngày (năm không quan trọng)")
            
        if st.button("Lưu sự kiện"):
            day_month = date_selected.strftime("%d/%m")
            st.session_state.events.append({"Tên": name, "Ngày": day_month, "Loại": event_type})
            st.success(f"Đã lưu: {name}")

    # --- PHẦN 2: HIỂN THỊ DANH SÁCH ---
    st.write("---")
    st.subheader("🔔 Danh sách sự kiện")
    
    if st.session_state.events:
        df = pd.DataFrame(st.session_state.events)
        
        # Logic tính toán ngày sắp tới (Đơn giản hóa)
        st.table(df)
        
        if st.button("Xóa tất cả"):
            st.session_state.events = []
            st.rerun()
    else:
        st.info("Chưa có sự kiện nào được tạo.")

    # --- PHẦN 3: TRA CỨU NHANH ---
    st.sidebar.header("Tra cứu âm lịch")
    check_date = st.sidebar.date_input("Chọn ngày dương muốn xem âm lịch")
    lunar_res = get_lunar_date(check_date)
    st.sidebar.success(f"Ngày âm tương ứng: {lunar_res}")

if __name__ == "__main__":
    main()
