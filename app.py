import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import requests
from lunar_python import Lunar, Solar

st.set_page_config(page_title="Quản Lý Sự Kiện Gia Đình", page_icon="📅", layout="wide")

# --- HÀM GỬI TELEGRAM ---
def send_telegram(message):
    try:
        token = st.secrets["telegram_token"]
        chat_id = st.secrets["telegram_chat_id"]
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"})
    except:
        pass

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
            # Lấy ngày chưa qua hoặc chỉ mới qua hôm nay (>= -1 để giữ ngày hiện tại)
            if (dt_solar.date() - now.date()).days >= -1:
                potential_dates.append(dt_solar)
        except: continue
    return min(potential_dates) if potential_dates else None

def get_sheet():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n")
        creds = Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds).open_by_key(st.secrets["sheet_id"]).get_worksheet(0)
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
    
    # --- HIỂN THỊ NGÀY HÔM NAY ---
    now = datetime.now()
    lunar_now = Lunar.fromDate(now)
    nam_viet = lunar_now.getYearInGanZhiByLiChun()
    
    st.markdown(f"""
    <div style="background-color: #1E3A8A; padding: 20px; border-radius: 10px; border-left: 10px solid #F87171; color: white; margin-bottom: 20px;">
        <h2 style="margin:0; color: white;">☀️ Dương lịch: {now.strftime('%d/%m/%Y')}</h2>
        <h3 style="margin:0; color: #FCD34D;">🌙 Âm lịch: Ngày {lunar_now.getDay()}/{lunar_now.getMonth()} - Năm {nam_viet}</h3>
        <p style="margin:0; font-style: italic;">🎋 Tiết khí: {lunar_now.getJieQi() if lunar_now.getJieQi() else "Bình thường"}</p>
    </div>
    """, unsafe_allow_html=True)

    sheet = get_sheet()
    if sheet:
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        days_left_list = []
        messages_to_send = []

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
                
                # --- LOGIC GỬI LIÊN TỤC TỪ 3 NGÀY ĐẾN 0 NGÀY ---
                if 0 <= diff <= 3:
                    prefix = "🔴 HÔM NAY" if diff == 0 else f"🔔 Còn {diff} ngày"
                    messages_to_send.append(f"{prefix}: *{row['Tên']}* ({row['Ngày']})")
            except: 
                days_left_list.append(999)

        # Gửi thông báo tự động (mỗi lần mở app sẽ kiểm tra)
        if messages_to_send:
            # Tạo một khóa để tránh gửi lặp quá nhiều lần trong 1 phiên làm việc
            current_check = ",".join(messages_to_send)
            if st.session_state.get('last_notified') != current_check:
                full_msg = "📢 *NHẮC NHỞ SỰ KIỆN SẮP TỚI:*\n" + "\n".join(messages_to_send)
                send_telegram(full_msg)
                st.session_state.last_notified = current_check

        df['Sắp đến (ngày)'] = days_left_list
        df = df.sort_values(by='Sắp đến (ngày)')

        # --- BẢNG DANH SÁCH ---
        st.subheader("📋 Danh sách sự kiện")
        for index, row in df.iterrows():
            col_t1, col_t2, col_t3, col_t4, col_b1, col_b2 = st.columns([3, 2, 2, 2, 1, 1])
            with col_t1: st.write(f"**{row['Tên']}**")
            with col_t2: st.write(row['Ngày'])
            with col_t3: st.write(row['Loại'])
            with col_t4: 
                if 0 <= row['Sắp đến (ngày)'] <= 3:
                    st.markdown(f"<span style='color:red; font-weight:bold;'>🔥 {row['Sắp đến (ngày)']} ngày</span>", unsafe_allow_html=True)
                elif row['Sắp đến (ngày)'] <= 7:
                    st.markdown(f"<span style='color:orange; font-weight:bold;'>{row['Sắp đến (ngày)']} ngày</span>", unsafe_allow_html=True)
                else:
                    st.write(f"{row['Sắp đến (ngày)']} ngày")
            
            with col_b1:
                if st.button("🗑️", key=f"del_{index}"):
                    cell = sheet.find(row['Tên'])
                    sheet.delete_rows(cell.row)
                    st.rerun()
            with col_b2:
                if st.button("📝", key=f"edit_{index}"):
                    st.session_state.editing_row = row['Tên']
            st.divider()

        # --- FORM SỬA / THÊM MỚI (Giữ nguyên) ---
        if "editing_row" in st.session_state:
            with st.form("edit_form"):
                st.info(f"Đang sửa: {st.session_state.editing_row}")
                new_name = st.text_input("Tên mới", value=st.session_state.editing_row)
                new_date = st.text_input("Ngày mới (VD: 27/12)")
                if st.form_submit_button("Cập nhật"):
                    cell = sheet.find(st.session_state.editing_row)
                    sheet.update_cell(cell.row, 1, new_name)
                    if new_date: sheet.update_cell(cell.row, 2, new_date)
                    del st.session_state.editing_row
                    st.rerun()

        with st.expander("➕ Thêm sự kiện mới"):
            with st.form("add_new"):
                n = st.text_input("Tên:")
                d = st.text_input("Ngày (VD: 15/05):")
                l = st.selectbox("Loại:", ["Âm lịch", "Dương lịch"])
                if st.form_submit_button("Lưu"):
                    if n and d:
                        sheet.append_row([n, d, l])
                        st.rerun()
