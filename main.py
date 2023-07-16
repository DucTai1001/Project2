import streamlit as st
import pickle
from pathlib import Path
import streamlit_authenticator as stauth
import streamlit as st
import json
import pandas as pd
from io import StringIO
import plotly.graph_objects as go
import pymysql
from datetime import datetime
from streamlit_option_menu import option_menu
from plotly.subplots import make_subplots
import altair as alt
from streamlit_lightweight_charts import renderLightweightCharts
st.set_page_config(
    page_title="Monitoring and Alerting Stock Market",
    page_icon="💸",layout="wide")
with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
#Kết nôi database
conn = st.experimental_connection(
        "local_db",
        type="sql",
        url="mysql://root:taimysql1001@127.0.0.1:3306/project2"
    )
with st.sidebar:
    select = option_menu(menu_title="Main Menu", options=["Dashboard", "Alert"])
if(select == "Dashboard"):
#Đoạn đầu
    lastest_date = "select max(date_key) as date from project2.price_change"
    lastest_date = conn.query(lastest_date)
    lastest_date = lastest_date['date'].iloc[0]
    change_hot_ticker = f"select max(percent_change) as max_change from project2.price_change where date_key = {lastest_date}"
    change_hot_ticker = conn.query(change_hot_ticker)
    hot_ticker = f"select Ticker from project2.price_change where date_key = {lastest_date} and percent_change = {change_hot_ticker['max_change'].iloc[0]}"
    hot_ticker = conn.query(hot_ticker)
    change_hot_ticker = change_hot_ticker['max_change'].iloc[0]
    hot_ticker = hot_ticker['Ticker'].iloc[0]

    change_worst_ticker = f"select min(percent_change) as min_change from project2.price_change where date_key = {lastest_date}"
    change_worst_ticker = conn.query(change_worst_ticker)
    worst_ticker = f"select Ticker from project2.price_change where date_key = {lastest_date} and percent_change = {change_worst_ticker['min_change'].iloc[0]}"
    worst_ticker = conn.query(worst_ticker)
    change_worst_ticker=change_worst_ticker['min_change'].iloc[0]
    worst_ticker = worst_ticker['Ticker'].iloc[0]

    def sector(lastest_date):
        query_sector = f"select Ticker,Close,sector ,market_cap, sum(market_cap) over (partition by sector) as sector_cap from (SELECT f.Ticker,f.Close, f.market_cap, c.sector FROM dim_company c, fact_stock_analysis f WHERE c.Ticker = f.Ticker AND f.Date_key = {lastest_date}) as sector;"
        sector = conn.query(query_sector)
        sector['weight'] = sector.apply(lambda row: row['market_cap'] / row['sector_cap'], axis=1)
        sector['price_weight'] = sector.apply(lambda row: row['Close']*row['weight'], axis=1)
        sector_sum = sector.groupby('sector')['price_weight'].sum()
        return sector_sum
    sector_sum_now = sector(lastest_date)
    # sector_sum_now
    pre_lastest_date = f"select max(date_key) as date from project2.price_change where date_key < {lastest_date}"
    pre_lastest_date = conn.query(pre_lastest_date)
    pre_lastest_date = pre_lastest_date['date'].iloc[0]
    sector_sum_pre = sector(pre_lastest_date)
    # sector_sum_pre
    compare_sector = pd.merge(sector_sum_now, sector_sum_pre, on='sector')
    compare_sector = compare_sector.rename(columns={'price_weight_x': 'now','price_weight_y': 'pre'})

    compare_sector['per_change'] = (compare_sector['now'] - compare_sector['pre'])/compare_sector['pre']*100
    compare_sector['per_change']=compare_sector['per_change'].round(2)
    hot_sector = compare_sector[compare_sector['per_change'] == max(compare_sector['per_change'])]
    hot_percent = hot_sector.iloc[0][2]
    hot_sector = hot_sector.index.values
    # hot_sector[0]

    worst_sector = compare_sector[compare_sector['per_change'] == min(compare_sector['per_change'])]
    worst_percent = worst_sector.iloc[0][2]
    worst_sector = worst_sector.index.values
    # worst_sector[0]


    col1, col2, col3, col4 = st.columns(4)

    with col1:
        col1.metric(label="HOTTEST SECTOR", value=hot_sector[0], delta=str(hot_percent) + '%',)


    with col2:
        col2.metric(label="WORST SECTOR", value=worst_sector[0], delta=str(worst_percent) + '%',)

    with col3:
        col3.metric(label="TOP STOCK", value=hot_ticker, delta = str(change_hot_ticker) +'%'
                      )
    with col4:
            col4.metric(label="WORST STOCK", value = worst_ticker, delta=str(change_worst_ticker) + '%')

    #Đoạn 2
    container1 = st.container()


    with container1:

        p1_col1, p1_col2 = st.columns([4,2])
        with p1_col1:

            COLOR_BULL = 'rgba(38,166,154,0.9)'  # #26a69a
            COLOR_BEAR = 'rgba(239,83,80,0.9)'
            # Nhập cần tìm kiếm
            col5,col3, col4 = st.columns([8,2, 2])
            with col5:
                st.subheader(f"PRICE AND VOLUME SERIES CHART: ")
            # with col1:
            #     start_date = st.date_input(label='dâte', label_visibility="hidden")
            #     start_date = str(start_date)
            #     start_date = start_date.replace("-", "")
            #     start_date = int(start_date)
            #
            # with col2:
            #     end_date = st.date_input(label='d1âte', label_visibility="hidden")
            #     end_date = str(end_date)
            #     end_date = end_date.replace("-", "")
            #     end_date = int(end_date)

            with col3:
                symbol = st.text_input(label="stock hi", value="AAA", label_visibility="hidden",
                                       placeholder='Ticker & Enter press...')
            with col4:
                option = ['Daily', 'Weekly', 'Monthly']
                otp = st.selectbox(label='select box', options=option, label_visibility="hidden")

            start_date = f'select min(date_key) as min from dim_time'
            start_date=conn.query(start_date)
            start_date = start_date['min'].iloc[0]


            end_date = f'select max(date_key) as max from dim_time'
            end_date=conn.query(end_date)
            end_date = end_date['max'].iloc[0]

            if (otp == 'Daily'):
                table = 'fact_stock_analysis'
            if (otp == 'Weekly'):
                table = 'weekly'
            query = f"select t.date, f.Open, f.High, f.Low, f.Close, f.Volume from dim_time t, {table} f where t.date_key = f.Date_key and Ticker = '{symbol}' and f.Date_key <= {end_date} and f.Date_key >= {start_date} order by t.date asc"

            price_volume = conn.query(query)

            price_volume.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
            price_volume['time'] = pd.to_datetime(price_volume['date']).dt.strftime("%Y-%m-%d")
            candles = json.loads(price_volume.to_json(orient="records"))
            volume = json.loads(price_volume.rename(columns={"volume": "value", }).to_json(orient="records"))
            priceVolumeChartOptions = {
                "height": 400,
                "rightPriceScale": {
                    "scaleMargins": {
                        "top": 0.2,
                        "bottom": 0.25,
                    },
                    "borderVisible": False,
                },
                "overlayPriceScales": {
                    "scaleMargins": {
                        "top": 0.7,
                        "bottom": 0,
                    }
                },
                "layout": {
                    "background": {
                        "type": 'solid',
                        "color": 'white'
                    },
                    "textColor": 'black',
                },
                "grid": {
                    "vertLines": {
                        "color": "rgba(197, 203, 206, 0.5)",
                    },
                    "horzLines": {
                        "color": "rgba(197, 203, 206, 0.5)",
                    }
                },
                "crosshair": {
                    "mode": 0
                }
            }
            priceVolumeSeries = [
                {
                    "type": 'Candlestick',
                    "data": candles,
                    "options": {
                        "upColor": COLOR_BULL,
                        "downColor": COLOR_BEAR,
                        "borderVisible": False,
                        "wickUpColor": COLOR_BULL,
                        "wickDownColor": COLOR_BEAR
                    }
                },
                {
                    "type": 'Histogram',
                    "data": volume,
                    "options": {
                        "color": '#26a69a',
                        "priceFormat": {
                            "type": 'volume',
                        },
                        "priceScaleId": ""  # set as an overlay setting,
                    },
                    "priceScale": {
                        "scaleMargins": {
                            "top": 0.7,
                            "bottom": 0,
                        }
                    }
                }
            ]
            renderLightweightCharts([
                {
                    "chart": priceVolumeChartOptions,
                    "series": priceVolumeSeries
                }
            ], 'priceAndVolume')

    #Phần 3:
    container3 = st.container()
    with container3:
        p3_col1, p3_col2, p3_col3 = st.columns([2,2,3])
        with p3_col3:
            p4_col1, p4_col2 = st.columns([5, 1])
            with p4_col1:
                st.subheader(f'COMPARE PRICE: \n A historica comparison of how {symbol} moves with different tickers.')
            with p4_col2:
                symbol1 = st.text_input(label="Symbol", value="AAA", label_visibility="hidden",
                                            placeholder='Ticker & Enter press...')
            # with p3_col2:
            #     symbol1 = st.text_input(label="Symbol", value="AAA",label_visibility="hidden",
            #                                    placeholder='Ticker & Enter press...')
            query = f"select d.date, f.Close from fact_stock_analysis f, dim_time d where f.Date_key = d.date_key and Ticker = '{symbol1}'"
            sym = conn.query(query)

            query2 = f"select d.date, f.Close from fact_stock_analysis f, dim_time d where f.Date_key = d.date_key and Ticker = '{symbol}'"
            sym1 = conn.query(query2)

            fig = go.Figure()

            fig.add_trace(go.Scatter(x=sym['date'], y=sym['Close'],
                                         mode='lines', name=symbol1,
                                         line=dict(color='red')))
            fig.add_trace(go.Scatter(x=sym1['date'], y=sym1['Close'],
                                         mode='lines', name=symbol))

            fig.update_layout(
                    xaxis_title='Date',
                    yaxis_title='Price',
                    plot_bgcolor='white',
                    height = 400,
                     width = 600
            )
                # title='Account Length by State',
            fig

        with p3_col1:
            count_mon = conn.query(f"select Monday from dow where Date = {lastest_date} and Ticker ='{symbol}'")
            count_tues = conn.query(f"select Tuesday from dow where Date = {lastest_date} and Ticker ='{symbol}'")
            count_fri = conn.query(f"select Friday from dow where Date = {lastest_date} and Ticker ='{symbol}'")
            count_wed = conn.query(f"select Wednesday from dow where Date = {lastest_date} and Ticker ='{symbol}'")
            count_thurs = conn.query(f"select Thursday from dow where Date = {lastest_date} and Ticker ='{symbol}'")
            per_mon = round(count_mon / 168 * 100, 2)
            per_tues = round(count_tues / 168 * 100, 2)
            per_fri = round(count_fri / 168 * 100, 2)
            per_wed = round(count_wed / 168 * 100, 2)
            per_thurs = round(count_thurs / 168 * 100, 2)
            percent = [per_mon.values[0][0], per_tues.values[0][0], per_wed.values[0][0], per_thurs.values[0][0],
                       per_fri.values[0][0]]

            st.subheader('WEEK DAY SEASONALITY: \n Percentage of green days for every week day')

            fig = go.Figure(data=go.Scatterpolar(
                r=percent,
                theta=['Mon', 'Tue', 'Wed', 'Thurs', 'Fri'],
                fill='toself',
                marker=dict(color='#99FFFF')
            ))
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True
                    ),
                ),
                showlegend=False,
                height=400,
                width=400
            )
            fig

        with p3_col2:
            count_jan = conn.query(
                f"select static_month.1 from static_month where Date = {lastest_date} and Ticker ='{symbol}'")
            count_feb = conn.query(
                f"select static_month.2 from static_month where Date = {lastest_date} and Ticker ='{symbol}'")
            count_mar = conn.query(
                f"select static_month.3 from static_month where Date = {lastest_date} and Ticker ='{symbol}'")
            count_apr = conn.query(
                f"select static_month.4 from static_month where Date = {lastest_date} and Ticker ='{symbol}'")
            count_may = conn.query(
                f"select static_month.5 from static_month where Date = {lastest_date} and Ticker ='{symbol}'")
            count_jun = conn.query(
                f"select static_month.6 from static_month where Date = {lastest_date} and Ticker ='{symbol}'")
            count_jul = conn.query(
                f"select static_month.7 from static_month where Date = {lastest_date} and Ticker ='{symbol}'")
            count_aug = conn.query(
                f"select static_month.8 from static_month where Date = {lastest_date} and Ticker ='{symbol}'")
            count_sep = conn.query(
                f"select static_month.9 from static_month where Date = {lastest_date} and Ticker ='{symbol}'")
            count_oct = conn.query(
                f"select static_month.10 from static_month where Date = {lastest_date} and Ticker ='{symbol}'")
            count_nov = conn.query(
                f"select static_month.11 from static_month where Date = {lastest_date} and Ticker ='{symbol}'")
            count_dec = conn.query(
                f"select static_month.12 from static_month where Date = {lastest_date} and Ticker ='{symbol}'")

            per_jan = round(count_jan / 72 * 100, 2)
            per_feb = round(count_feb / 72 * 100, 2)
            per_mar = round(count_mar / 72 * 100, 2)
            per_apr = round(count_apr / 72 * 100, 2)
            per_may = round(count_may / 72 * 100, 2)
            per_jun = round(count_jun / 72 * 100, 2)
            per_jul = round(count_jul / 72 * 100, 2)
            per_aug = round(count_aug / 72 * 100, 2)
            per_sep = round(count_sep / 72 * 100, 2)
            per_oct = round(count_oct / 72 * 100, 2)
            per_nov = round(count_nov / 72 * 100, 2)
            per_dec = round(count_dec / 72 * 100, 2)

            percent1 = [per_jan.values[0][0], per_feb.values[0][0], per_mar.values[0][0], per_apr.values[0][0],
                        per_may.values[0][0], count_jun.values[0][0], count_jul.values[0][0], count_aug.values[0][0],
                        per_sep.values[0][0], per_oct.values[0][0], per_nov.values[0][0], per_dec.values[0][0]]
            st.subheader('MONTHLY SEASONALITY: \n Percentage of times each month closes green')

            fig = go.Figure(data=go.Scatterpolar(
                r=percent1,
                theta=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                fill='toself',
                marker=dict(color='#99FFFF')
            ))
            fig.update_layout(

                polar=dict(
                    radialaxis=dict(
                        visible=True
                    ),
                ),
                showlegend=False,
                height=400,
                width=400
            )
            fig

    #Phần 4
    container4 = st.container()
    with container4:
        p4_col1, p4_col2 = st.columns([6,4])


        with p4_col1:
            st.subheader('MARKET OVERVIEW:')
            query = f"SELECT rank2.Ticker, rank2.percent_change, rank2.Sector, rank2.market_cap, rank2.rank1 \
            FROM (SELECT sum.Ticker, sum.percent_change, sum.Sector, sum.market_cap, DENSE_RANK() OVER (PARTITION BY sum.Sector ORDER BY sum.market_cap DESC) AS rank1 \
                  FROM (SELECT c.Ticker, p.percent_change, c.Sector, f.market_cap \
                        FROM dim_company c, fact_stock_analysis f, price_change p \
                        WHERE c.Ticker = f.Ticker \
                          AND p.Ticker = c.Ticker \
                          AND p.date_key = {lastest_date} \
                          AND f.date_key = {lastest_date}) AS sum) AS rank2 \
            WHERE rank2.rank1 <= 6;"

            merged_df1 = conn.query(query)

            import plotly.express as px


            def get_chart_30507420():
                merged_df1['Color'] = 'default'  # Tạo cột 'Color' với giá trị mặc đị
                # Định nghĩa các điều kiện và màu sắc tương ứng
                # Tăng
                merged_df1.loc[
                    (0 <= merged_df1['percent_change']) & (merged_df1['percent_change'] < 0.003), 'Color'] = '#9AFF9A'
                merged_df1.loc[
                    (0.003 <= merged_df1['percent_change']) & (merged_df1['percent_change'] < 0.005), 'Color'] = '#00EE76'
                merged_df1.loc[
                    (0.005 <= merged_df1['percent_change']) & (merged_df1['percent_change'] < 0.0075), 'Color'] = '#00CD66'
                merged_df1.loc[(0.0075 <= merged_df1['percent_change']), 'Color'] = '#008B45'
                # Giảm
                merged_df1.loc[
                    (-0.002 < merged_df1['percent_change']) & (merged_df1['percent_change'] < 0), 'Color'] = '#FF6347'
                merged_df1.loc[
                    (-0.005 < merged_df1['percent_change']) & (merged_df1['percent_change'] <= -0.002), 'Color'] = '#EE5C42'
                merged_df1.loc[(-0.0082 < merged_df1['percent_change']) & (
                            merged_df1['percent_change'] <= -0.005), 'Color'] = '#CD4F39'
                merged_df1.loc[(merged_df1['percent_change'] <= -0.0082), 'Color'] = '#8B3626'

                color1 = {'(?)': '#FFFFFF'}

                for i in range(merged_df1.shape[0]):
                    key = merged_df1.iloc[i]['Ticker']
                    value = merged_df1.iloc[i]['Color']
                    color1[key] = value

                fig = px.treemap(merged_df1, path=['Sector', 'Ticker'],
                                 values='market_cap', color='Ticker',
                                 color_discrete_map=color1)
                fig.update_layout(margin=dict(t=60, l=25, r=25, b=25))
                fig.data[0].customdata = merged_df1['percent_change'].tolist()
                ids = fig.data[0].ids
                result = [item.split('/')[1] for item in ids if '/' in item]
                customdata = []
                for i in result:
                    customdata.append(merged_df1[merged_df1['Ticker'] == i]['percent_change'].values[0])
                fig.data[0].customdata = customdata
                fig.update_traces(
                    textfont=dict(
                        family=' Segoe UI',
                        size=16,
                    ),
                    selector=dict(type='treemap')
                )
                fig.data[
                    0].texttemplate = "<b><span style='font-size: 24px; font-family: Arial;'>%{label}</span></b> <br> <br> <span style='font-size: 16px'> %{customdata}</span>%<br>"
                fig.update_layout(width=750, height=400)
                st.plotly_chart(fig, theme="streamlit")
            get_chart_30507420()

        with p4_col2:
            st.subheader('SECTOR PERFORMANCE:')
            st.subheader('')
            st.subheader('')
            st.subheader('')
            import altair as alt

            # Đảm bảo rằng bạn đã import thư viện Altair và reset index của DataFrame
            compare_sector = compare_sector.reset_index()
            compare_sector = compare_sector[['sector', 'per_change']]

            # Vẽ biểu đồ cột
            bar_chart = alt.Chart(compare_sector).mark_bar().encode(
                x=alt.X('per_change', title='Percentage Change'),
                y=alt.Y('sector', sort='-x', title='Sector'),
                color=alt.condition(
                    alt.datum.per_change >= 0,
                    alt.value('green'),  # Màu xanh cho giá trị per_change >= 0
                    alt.value('red')  # Màu đỏ cho giá trị per_change < 0
                )
            )
            # Hiển thị biểu đồ

            st.markdown('<style>body{background-color: white;}</style>', unsafe_allow_html=True)
            st.altair_chart(bar_chart, use_container_width=True)

if(select == "Alert"):
    import smtplib
    import time
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText


    def send_email(mess):
        email = "ductaile1001@gmail.com"
        password = "tmelgvoydslfjuez"
        email_sent = "taimanutd10012001@gmail.com"

        # Tạo đối tượng MIMEMultipart
        message = MIMEMultipart()
        message['From'] = email
        message['To'] = email_sent
        message['Subject'] = 'Cảnh báo chứng khoán:   '

        # Nội dung email
        mail_content = mess
        message.attach(MIMEText(mail_content, 'plain'))

        # Gửi email
        try:
            session = smtplib.SMTP('smtp.gmail.com', 587)
            session.starttls()
            session.login(email, password)
            session.sendmail(email, email_sent, message.as_string())
            session.quit()
            print('Email đã được gửi thành công!')
        except Exception as e:
            print('Gửi email không thành công. Lỗi:', str(e))


    import streamlit as st
    import pickle
    from pathlib import Path
    import streamlit_authenticator as stauth
    import streamlit as st
    import pandas as pd
    from io import StringIO
    import plotly.graph_objects as go
    import pymysql
    from datetime import datetime
    from streamlit_option_menu import option_menu
    from plotly.subplots import make_subplots
    import numpy as np

    import streamlit as st

    st.subheader('Price Target')
    con1 = st.container()
    with con1:

        up_col1, up_col2, up_col3 = st.columns([2, 4, 1])

        with up_col1:
            symbol_upper = st.text_input('Upper Limit Price Target', placeholder='Enter Ticker')
        with up_col2:
            try:
                price_upper = st.text_input(' Price Target ', placeholder='Enter upper limit price target')
                price_upper = float(price_upper)
            except ValueError:
                pass
        with up_col3:
            upper_status = 0
            st.header('')
            if (st.button('Add Alert')):
                upper_status = 1
    con2 = st.container()
    with con2:

        low_col1, low_col2, low_col3, low_col4 = st.columns(4)
        with up_col1:
            symbol_lower = st.text_input('Lower Limit Price Target', placeholder='Enter Ticker')
        with up_col2:
            try:
                price_lower = st.text_input(' Price Target', placeholder='Enter lower limit price target')
                price_lower = float(price_lower)
            except ValueError:
                pass
        with up_col3:
            lower_status = 0

            st.header(' ')

            if (st.button('Add Alert ')):
                lower_status = 1


    def send_email(mess):
        email = "ductaile1001@gmail.com"
        password = "tmelgvoydslfjuez"
        email_sent = "taimanutd10012001@gmail.com"

        # Tạo đối tượng MIMEMultipart
        message = MIMEMultipart()
        message['From'] = email
        message['To'] = email_sent
        message['Subject'] = 'Cảnh báo chứng khoán:   '

        # Nội dung email
        mail_content = mess
        message.attach(MIMEText(mail_content, 'plain'))

        # Gửi email
        try:
            session = smtplib.SMTP('smtp.gmail.com', 587)
            session.starttls()
            session.login(email, password)
            session.sendmail(email, email_sent, message.as_string())
            session.quit()
            print('Email đã được gửi thành công!')
        except Exception as e:
            print('Gửi email không thành công. Lỗi:', str(e))


    st.subheader('Simple Moving Average Technical')

    con1 = st.container()
    with con1:

        up_col1, up_col2, up_col3 = st.columns([2, 4, 1])

        with up_col1:
            gol_symbol = st.text_input('Golden Cross Patternd', label_visibility="visible", placeholder='Enter Ticker')

        with up_col2:
            gol_status = 0
            st.header('')
            if (st.button('Add Alert  ')):
                gol_status = 1
    con2 = st.container()
    with con2:

        low_col1, low_col2, low_col3, low_col4 = st.columns(4)
        with up_col1:
            de_symbol = st.text_input('Death Cross Pattern', label_visibility="visible", placeholder='Enter Ticker')

        # with up_col3:
        #     try:
        #         price_lower = st.text_input(' Price Target',placeholder = 'Enter lower limit price target')
        #         price_lower = float(price_lower)
        #     except ValueError:
        #         pass
        with up_col2:
            de_status = 0

            st.header(' ')

            if (st.button('Add Alert    ')):
                de_status = 1
    if (de_status == 1 or gol_status == 1 or lower_status == 1 or upper_status == 1):
        while (True):
            ######price targer
            import mysql.connector

            # Thiết lập kết nối
            cnx = mysql.connector.connect(
                host="localhost",
                user="root",
                password="taimysql1001",
                database="project2"
            )
            cursor = cnx.cursor()

            time1 = "select max(Time) FROM real_time"
            cursor.execute(time1)
            # Lấy kết quả truy vấn
            time1 = cursor.fetchall()

            time_now = time1[0]
            time_now = time_now[0].strftime("%Y-%m-%d %H:%M:%S")

            # Thực hiện truy vấn SQL

            if (symbol_upper):
                query_up = f"SELECT Price FROM real_time where Ticker = '{symbol_upper}' and Time = '{time_now}';"
                cursor.execute(query_up)
                # Lấy kết quả truy vấn
                result_up = cursor.fetchall()
                price_now_up = result_up[0][0]

            if (symbol_lower):
                query_low = f"SELECT Price FROM real_time where Ticker = '{symbol_lower}' and Time = '{time_now}';"
                cursor.execute(query_low)
                # Lấy kết quả truy vấn
                result_low = cursor.fetchall()
                price_now_low = result_low[0][0]
            cursor.close()
            cnx.close()
            try:
                if ((price_upper <= price_now_up) & (upper_status == 1)):
                    mess = f'Giá trị cổ phiếu {symbol_upper} đã vượt qua {price_upper}'
                    send_email(mess)
                if ((price_lower >= price_now_low) & (lower_status == 1)):
                    mess = f'Giá trị cổ phiếu {symbol_lower} đã tụt xuống {price_upper}'
                    send_email(mess)
            except:
                pass
            ##############Technical
            # Thiết lập kết nối
            cnx = mysql.connector.connect(
                host="localhost",
                user="root",
                password="taimysql1001",
                database="project2"
            )
            cursor = cnx.cursor()
            # max_date
            max_date = f"SELECT max(Date) FROM gold_death ;"
            cursor.execute(max_date)
            result = cursor.fetchall()
            max_date = result[0][0]
            max2_date = f"select max(Date) from gold_death where Date != {max_date}"
            cursor.execute(max2_date)
            result = cursor.fetchall()
            max2_date = result[0][0]
            gold_pre = 6
            gold = 6
            if (gol_symbol):
                # Cảnh báo với gold pattern
                gold = f"SELECT Gold_Cross FROM gold_death where Ticker = '{gol_symbol}' and Date = {max_date};"

                cursor.execute(gold)
                result = cursor.fetchall()
                gold_pre = result[0][0]

                #
                gold1 = f"SELECT Gold_Cross  FROM gold_death where Ticker = '{gol_symbol}' and Date = {max2_date};"
                cursor.execute(gold1)
                result = cursor.fetchall()
                gold = result[0][0]

                # Cảnh báo với death_patten
            death = 6
            death_pre = 6
            if (de_symbol):
                death = f"SELECT Death_Cross FROM gold_death where Ticker = '{de_symbol}' and Date = {max_date};"
                cursor.execute(death)
                result1 = cursor.fetchall()
                death_pre = result1[0][0]

                death1 = f"SELECT Death_Cross  FROM gold_death where Ticker = '{de_symbol}' and Date = {max2_date};"

                cursor.execute(death1)
                result2 = cursor.fetchall()
                death = result2[0][0]

            cursor.close()
            cnx.close()
            if ((gold_pre == 1) & (gold == 0)):
                mess = f'Hệ thống phát hiện tín hiệu điểm Gold Cross!'
                send_email(mess)
            if ((death_pre == 1) & (death == 0)):
                mess = f'Hệ thống phát hiện tín hiệu điểm Death Cross!'
                send_email(mess)
            time.sleep(60)