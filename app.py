import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
import pandas as pd
import os

# Отключаем watchdog для избежания ошибки inotify
os.environ['STREAMLIT_SERVER_WATCH_DIR'] = 'false'

# Настройка страницы
st.set_page_config(page_title="Team Registration", layout="centered")

# Загрузка учетных данных Google
@st.cache_resource
def get_google_creds():
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    return credentials

# Функция для получения данных из Google Sheets
@st.cache_data(ttl=60)  # Кэширование на 60 секунд
def get_sheet_data(sheet_name):
    try:
        credentials = get_google_creds()
        service = build('sheets', 'v4', credentials=credentials)
        
        spreadsheet_id = st.secrets["spreadsheet_id"]
        range_name = f'{sheet_name}!A:Z'
        
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()
        
        return result.get('values', [])
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return []

# Получение контента из B2B Inputs
def get_content(content_type, b2b_data):
    try:
        df = pd.DataFrame(b2b_data[1:], columns=b2b_data[0])
        content_row = df[df['Content Type'] == content_type]
        return content_row['Content'].iloc[0] if not content_row.empty else ""
    except Exception as e:
        st.error(f"Error getting content: {str(e)}")
        return ""

# Загрузка данных
try:
    b2b_data = get_sheet_data('B2B Inputs')
    timeslots_data = get_sheet_data('Timeslots')

    # Получение необходимого контента
    welcome_text = get_content('welcome_text', b2b_data)
    welcome_image = get_content('welcome_image', b2b_data)
    importance_text = get_content('importance_text', b2b_data)
    importance_image = get_content('importance_image', b2b_data)
    team_codes = get_content('team_codes', b2b_data).split(',')
    team_codes = [code.strip() for code in team_codes]

    # Форма
    with st.form("registration_form"):
        # Секция 1: Приветствие
        st.title(welcome_text)
        if welcome_image:
            st.image(welcome_image)
        
        # Валидация кода команды
        team_code = st.text_input(
            "Team Code",
            help="Enter your team code (e.g., MON001)"
        )
        
        # Секция 2: Важность встреч
        st.title("Team Calls")
        st.write(importance_text)
        if importance_image:
            st.image(importance_image)
        
        # Выбор времени
        if len(timeslots_data) > 1:  # Проверяем, что есть данные
            timeslots_df = pd.DataFrame(timeslots_data[1:], columns=timeslots_data[0])
            time_options = [
                f"{row['team_type']} | {row['team_day']} | {row['team_time']} ({row['team_users']} участников)"
                for _, row in timeslots_df.iterrows()
            ]
            time_options.append("Не смогу в это время")
            
            selected_times = st.multiselect(
                "Выберите удобное время",
                options=time_options,
                help="Выберите один или несколько вариантов"
            )
        
        # Кнопка отправки
        submitted = st.form_submit_button("Submit")

    # Обработка отправки формы
    if submitted:
        if team_code not in team_codes:
            st.error("Неверный код команды")
        elif not selected_times:
            st.error("Пожалуйста, выберите время")
        else:
            st.success("Спасибо! Ваш ответ записан.")

except Exception as e:
    st.error(f"An error occurred: {str(e)}")