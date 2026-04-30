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
    except: pass

# --- HÀM CHUYỂN ÂM SANG DƯƠNG (TỰ NHẢY NĂM) ---
def get_solar_from_lunar(lunar_day, lunar_month):
    now = datetime.now()
    # Kiểm tra năm nay và năm sau
    years = [now.year, now.year + 1]
    for y in years:
        try:
            lunar = Lunar.fromYmd(y, lunar_month, lunar_day)
            solar = lunar.getSolar()
            dt_solar = datetime(solar.getYear(), solar.getMonth(), solar.getDay())
            # Nếu ngày này chưa qua (hoặc là hôm nay)
            if (dt_solar.date() - now.date()).days >= 0:
                return dt_solar
        except: continue
    return None

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
    
    now = datetime.now()
    lunar_now = Lunar.fromDate(now)
    nam_viet = lunar_now.getYearInGanZhiByLiChun()
    
    st.markdown(f"""
    <div style="background-color: #1E3A8A; padding: 20px; border-radius: 10px; border-left: 10px solid #F87171; color: white; margin-bottom: 25px;">
        <h2 style="margin:0; color: white;">☀️ Dương lịch: {now.strftime('%d/%m/%Y')}</h2>
        <h3 style="margin:0; color: #FCD34D;">🌙 Âm lịch: Ngày {lunar_now.getDay()}/{lunar_now.getMonth()} - Năm {nam_viet}</h3>
        <p style="margin:0; font-style: italic;">🎋 Tiết khí: {lunar_now.getJieQi() if lunar_now.getJieQi() else "Bình thường"}</p>
    </div>
    """, unsafe_allow_html=True)

    sheet = get_sheet()
    if sheet:
        sheet = get_sheet()
    if sheet:
        # --- CẬP NHẬT MÚI GIỜ VÀ LẤY DỮ LIỆU ---
        import pytz
        tz = pytz.timezone('Asia/Ho_Chi_Minh')
        now = datetime.now(tz)
        
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        days_left_list = []
        solar_date_list = [] # Danh sách lưu ngày DL để hiển thị
        messages_to_send = []

        for index, row in df.iterrows():
            try:
                day, month = map(int, str(row['Ngày']).split('/'))
                if "Âm lịch" in str(row['Loại']):
                    # Tìm ngày DL cho sự kiện âm lịch (đã bao gồm logic nhảy năm)
                    # Chỉnh lại hàm get_solar_from_lunar một chút để dùng tz
                    lunar = Lunar.fromYmd(now.year, month, day)
                    solar = lunar.getSolar()
                    event_date = datetime(solar.getYear(), solar.getMonth(), solar.getDay(), tzinfo=tz)
                    
                    if (event_date.date() - now.date()).days < 0:
                        lunar = Lunar.fromYmd(now.year + 1, month, day)
                        solar = lunar.getSolar()
                        event_date = datetime(solar.getYear(), solar.getMonth(), solar.getDay(), tzinfo=tz)
                else:
                    event_date = datetime(now.year, month, day, tzinfo=tz)
                    if (event_date.date() - now.date()).days < 0:
                        event_date = datetime(now.year + 1, month, day, tzinfo=tz)
                
                solar_date_list.append(event_date.strftime('%d/%m/%Y'))
                diff = (event_date.date() - now.date()).days
                days_left_list.append(diff)
                
                if 0 <= diff <= 3:
                    prefix = "🔴 HÔM NAY" if diff == 0 else f"🔔 Còn {diff} ngày"
                    messages_to_send.append(f"{prefix}: *{row['Tên']}* ({row['Ngày']})")
            except: 
                days_left_list.append(999)
                solar_date_list.append("N/A")

        if messages_to_send:
            current_check = ",".join(messages_to_send)
            if st.session_state.get('last_notified') != current_check:
                send_telegram("📢 *NHẮC NHỞ SỰ KIỆN SẮP TỚI:*\n" + "\n".join(messages_to_send))
                st.session_state.last_notified = current_check

        df['Sắp đến'] = days_left_list
        df['Ngày DL'] = solar_date_list
        df = df.sort_values(by='Sắp đến')

        st.subheader("📋 Danh sách sự kiện")
        
        # Chia 7 cột để thêm cột Ngày DL
        h_col1, h_col2, h_col3, h_col4, h_col5, h_col6, h_col7 = st.columns([2.5, 1.2, 1.8, 1.2, 1.8, 0.6, 0.6])
        h_col1.write("**Tên sự kiện**")
        h_col2.write("**Ngày**")
        h_col3.write("**Ngày DL**")
        h_col4.write("**Loại**")
        h_col5.write("**Trạng thái**")
        st.divider()

        for index, row in df.iterrows():
            d = row['Sắp đến']
            bg_color = "transparent"
            text_color = "black"
            status_text = f"{d} ngày"
            
            if d == 0: bg_color = "#FEE2E2"; text_color = "#991B1B"; status_text = "🔥 Hôm nay"
            elif 1 <= d <= 3: bg_color = "#FEE2E2"; text_color = "#991B1B"; status_text = f"⏳ {d} ngày"
            elif 4 <= d <= 7: bg_color = "#FFEDD5"; text_color = "#9A3412"; status_text = f"🔔 {d} ngày"
            elif 8 <= d <= 30: bg_color = "#DCFCE7"; text_color = "#166534"; status_text = f"📅 {d} ngày"

            with st.container():
                st.markdown(f'<div style="background-color: {bg_color}; padding: 10px; border-radius: 5px; margin-bottom: -40px;"></div>', unsafe_allow_html=True)
                c1, c2, c3, c4, c5, c6, c7 = st.columns([2.5, 1.2, 1.8, 1.2, 1.8, 0.6, 0.6])
                with c1: st.markdown(f"<p style='color:{text_color}; font-weight:bold; margin-top:10px;'>{row['Tên']}</p>", unsafe_allow_html=True)
                with c2: st.markdown(f"<p style='color:{text_color}; margin-top:10px;'>{row['Ngày']}</p>", unsafe_allow_html=True)
                with c3: st.markdown(f"<p style='color:{text_color}; font-style:italic; margin-top:10px;'>{row['Ngày DL']}</p>", unsafe_allow_html=True)
                with c4: st.markdown(f"<p style='color:{text_color}; margin-top:10px;'>{row['Loại']}</p>", unsafe_allow_html=True)
                with c5: st.markdown(f"<p style='color:{text_color}; font-weight:bold; margin-top:10px;'>{status_text}</p>", unsafe_allow_html=True)
                with c6:
                    if st.button("🗑️", key=f"del_{index}"):
                        cell = sheet.find(row['Tên']); sheet.delete_rows(cell.row); st.rerun()
                with c7:
                    if st.button("📝", key=f"edit_{index}"):
                        st.session_state.editing_row = row['Tên']; st.rerun()
            st.write("")

        # --- PHẦN FORM SỬA VÀ THÊM MỚI GIỮ NGUYÊN PHÍA DƯỚI ---
        if "editing_row" in st.session_state:
            with st.form("edit_form"):
                st.info(f"Đang sửa: {st.session_state.editing_row}")
                new_name = st.text_input("Tên mới", value=st.session_state.editing_row)
                new_date = st.text_input("Ngày mới (VD: 27/12)")
                c_f1, c_f2 = st.columns(2)
                with c_f1:
                    if st.form_submit_button("Cập nhật"):
                        cell = sheet.find(st.session_state.editing_row)
                        sheet.update_cell(cell.row, 1, new_name)
                        if new_date: sheet.update_cell(cell.row, 2, new_date)
                        del st.session_state.editing_row; st.rerun()
                with c_f2:
                    if st.form_submit_button("Hủy"):
                        del st.session_state.editing_row; st.rerun()

        with st.expander("➕ Thêm sự kiện mới"):
            with st.form("add_new"):
                n = st.text_input("Tên:"); dt = st.text_input("Ngày (VD: 15/05):")
                l = st.selectbox("Loại:", ["Âm lịch", "Dương lịch"])
                if st.form_submit_button("Lưu"):
                    if n and dt: sheet.append_row([n, dt, l]); st.rerun()
