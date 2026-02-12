import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import requests
from lunar_python import Lunar, Solar

st.set_page_config(page_title="Quản Lý Sự Kiện Gia Đình", page_icon="📅", layout="wide")

# --- TỪ ĐIỂN TIẾNG VIỆT ---
def get_lunar_info_vi(lunar):
    # Ép thư viện trả về tiếng Việt chuẩn
    can = lunar.getYearGan()
    chi = lunar.getYearZhi()
    # Thư viện đôi khi trả về chữ Hán, mình map lại nếu cần hoặc dùng hàm getYearInGanZhi
    return f"{lunar.getYearInGanZhiByLiChun()}"

# --- HÀM CHUYỂN ÂM SANG DƯƠNG ---
def get_solar_from_lunar(lunar_day, lunar_month):
    now = datetime.now()
    years_to_check = [now.year - 1, now.year, now.year + 1]
    potential_dates = []
    for y in years_to_check:
        try:
            lunar = Lunar.fromYmd(y, lunar_month, lunar_day)
            solar = lunar.getSolar()
            dt_solar = datetime(solar.getYear(), solar.getMonth(), solar.getDay())
            if (dt_solar.date() - now.date()).days >= -1:
                potential_dates.append(dt_solar)
        except: continue
    return min(potential_dates) if potential_dates else None

def get_sheet():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n")
        creds = Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        return client.open_by_key(st.secrets["sheet_id"]).get_worksheet(0)
    except: return None

# --- GIAO DIỆN ---
if "password_correct" not in st.session_state:
    st.subheader("🔒 Đăng nhập hệ thống")
    pw = st.text_input("Mật khẩu:", type="password")
    if st.button("Vào hệ thống"):
        if pw == st.secrets["password"]:
            st.session_state.password_correct = True
            st.rerun()
else:
    st.title("📅 QUẢN LÝ SỰ KIỆN GIA ĐÌNH")
    
    # --- KHỐI HIỂN THỊ NGÀY HÔM NAY (MÀU NỔI BẬT) ---
    now = datetime.now()
    lunar_now = Lunar.fromDate(now)
    
    st.markdown(f"""
    <div style="background-color: #1E3A8A; padding: 20px; border-radius: 10px; border-left: 10px solid #F87171; color: white;">
        <h2 style="margin:0; color: white;">☀️ Dương lịch: {now.strftime('%d/%m/%Y')}</h2>
        <h3 style="margin:0; color: #FCD34D;">🌙 Âm lịch: Ngày {lunar_now.getDay()}/{lunar_now.getMonth()} - Năm {lunar_now.getYearInGanZhiByLiChun()}</h3>
        <p style="margin:0; font-style: italic;">🎋 Tiết khí: {lunar_now.getJieQi() if lunar_now.getJieQi() else "Thanh nhàn"}</p>
    </div>
    """, unsafe_allow_html=True)

    sheet = get_sheet()
    if sheet:
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        # Thêm cột index để dễ xóa/sửa
        df['ID'] = range(2, len(df) + 2) 
        
        days_left_list = []
        for index, row in df.iterrows():
            try:
                day, month = map(int, str(row['Ngày']).split('/'))
                if "Âm lịch" in str(row['Loại']):
                    event_date = get_solar_from_lunar(day, month)
                else:
                    event_date = datetime(now.year, month, day)
                    if (event_date.date() - now.date()).days < -1:
                        event_date = datetime(now.year + 1, month, day)
                diff = (event_date.date() - now.date()).days if event_date else 999
                days_left_list.append(diff)
            except: days_left_list.append(999)

        df['Sắp đến (ngày)'] = days_left_list
        df = df.sort_values(by='Sắp đến (ngày)')

        # --- TÔ MÀU BẢNG DANH SÁCH ---
        st.subheader("📋 Danh sách sự kiện")
        
        def highlight_urgent(row):
            if row['Sắp đến (ngày)'] <= 7:
                return ['background-color: #FFE4E6; color: #BE123C; font-weight: bold'] * len(row)
            return [''] * len(row)

        st.dataframe(df.style.apply(highlight_urgent, axis=1), use_container_width=True)

        # --- CHỨC NĂNG SỬA / XÓA ---
        st.write("---")
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("➕ Thêm sự kiện")
            with st.form("add_form", clear_on_submit=True):
                new_name = st.text_input("Tên sự kiện:")
                new_date = st.text_input("Ngày (VD: 27/12):")
                new_type = st.selectbox("Loại:", ["Âm lịch", "Dương lịch"])
                if st.form_submit_button("Lưu mới"):
                    if new_name and new_date:
                        sheet.append_row([new_name, new_date, new_type])
                        st.success("Đã thêm!")
                        st.rerun()

        with col2:
            st.subheader("🗑️ Xóa sự kiện")
            event_to_delete = st.selectbox("Chọn sự kiện muốn xóa:", df['Tên'].tolist())
            if st.button("Xác nhận Xóa"):
                # Tìm dòng dựa trên tên
                cell = sheet.find(event_to_delete)
                sheet.delete_rows(cell.row)
                st.warning(f"Đã xóa {event_to_delete}")
                st.rerun()

        # Chức năng Sửa nhanh
        with st.expander("📝 Sửa tên hoặc ngày sự kiện"):
            event_to_edit = st.selectbox("Chọn sự kiện muốn sửa:", df['Tên'].tolist(), key="edit_box")
            edit_name = st.text_input("Tên mới:", value=event_to_edit)
            # Lấy ngày cũ làm mặc định
            old_date = df[df['Tên'] == event_to_edit]['Ngày'].values[0]
            edit_date = st.text_input("Ngày mới:", value=old_date)
            
            if st.button("Cập nhật thay đổi"):
                cell = sheet.find(event_to_edit)
                sheet.update_cell(cell.row, 1, edit_name) # Cột 1 là Tên
                sheet.update_cell(cell.row, 2, edit_date) # Cột 2 là Ngày
                st.success("Đã cập nhật!")
                st.rerun()
