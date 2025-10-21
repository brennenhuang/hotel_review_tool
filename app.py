"""
Main Streamlit application for Smart Speaker Conversation Analysis Platform
智能音箱對話分析平台
"""

import streamlit as st
from datetime import datetime, timedelta
from data_processor import DataProcessor
from visualizations import Visualizer
from export_manager import ExportManager


# Page configuration
st.set_page_config(
    page_title="智能音箱對話分析平台",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #666;
    }
    .stAlert {
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables"""
    if 'data_processor' not in st.session_state:
        st.session_state.data_processor = DataProcessor()
    if 'visualizer' not in st.session_state:
        st.session_state.visualizer = Visualizer()
    if 'export_manager' not in st.session_state:
        st.session_state.export_manager = ExportManager()
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    if 'show_drilldown' not in st.session_state:
        st.session_state.show_drilldown = False
    if 'selected_risk_level' not in st.session_state:
        st.session_state.selected_risk_level = None


def upload_page():
    """Display upload page"""
    st.markdown('<div class="main-header">🎤 智能音箱對話分析平台</div>', unsafe_allow_html=True)
    st.markdown("---")

    st.write("### 📁 數據上傳")
    st.write("上傳包含智能音箱對話紀錄的 CSV 檔案開始分析")

    uploaded_file = st.file_uploader(
        "選擇 CSV 檔案",
        type=['csv'],
        help="支援拖曳上傳，最多 10,000 筆數據"
    )

    if uploaded_file is not None:
        with st.spinner('正在處理數據...'):
            success, message = st.session_state.data_processor.load_and_process_csv(uploaded_file)

            if success:
                st.success(message)
                st.session_state.data_loaded = True
                st.rerun()
            else:
                st.error(message)

    # Show instructions
    with st.expander("📖 使用說明"):
        st.markdown("""
        **支援的數據格式：**
        - 檔案格式：CSV
        - 最大筆數：10,000 筆
        - 必需欄位請參考 PRD 文件

        **功能概述：**
        - 📊 多維度數據可視化
        - 🔍 靈活的篩選與查詢
        - ⚠️ 回應時間風險監控
        - 💾 一鍵導出對話報告
        """)


def dashboard_page():
    """Display main dashboard page"""
    st.markdown('<div class="main-header">🎤 智能音箱對話分析平台</div>', unsafe_allow_html=True)

    # Reset data button
    col1, col2, col3 = st.columns([6, 1, 1])
    with col3:
        if st.button("🔄 重新上傳", use_container_width=True):
            st.session_state.data_loaded = False
            st.session_state.data_processor = DataProcessor()
            st.session_state.show_drilldown = False
            st.rerun()

    st.markdown("---")

    # Sidebar filters
    with st.sidebar:
        st.header("🔍 全域篩選器")
        st.write("選擇篩選條件以過濾整個儀表板的數據")

        # Get date range
        min_date, max_date = st.session_state.data_processor.get_date_range()

        # Time range filter
        st.subheader("📅 時間區間")
        if min_date and max_date:
            date_range = st.date_input(
                "選擇日期範圍",
                value=(min_date.date(), max_date.date()),
                min_value=min_date.date(),
                max_value=max_date.date(),
                key="date_range"
            )
            start_date = datetime.combine(date_range[0], datetime.min.time()) if len(date_range) > 0 else None
            end_date = datetime.combine(date_range[1], datetime.max.time()) if len(date_range) > 1 else start_date
        else:
            start_date, end_date = None, None

        # Response timecost filter
        st.subheader("⏱️ 回應耗時 (秒)")
        min_timecost, max_timecost = st.session_state.data_processor.get_timecost_range()
        timecost_range = st.slider(
            "選擇耗時範圍",
            min_value=float(min_timecost),
            max_value=float(min(max_timecost, 20.0)),  # Cap at 20s for better UX
            value=(float(min_timecost), float(min(max_timecost, 20.0))),
            step=0.1,
            key="timecost_range"
        )

        # Categorical filters
        st.subheader("🏨 分類篩選")

        hotels = st.session_state.data_processor.get_unique_values('hotel_name')
        selected_hotels = st.multiselect("飯店名稱", hotels, default=hotels, key="hotels")

        rooms = st.session_state.data_processor.get_unique_values('room_name')
        selected_rooms = st.multiselect("房間號碼", rooms, key="rooms")

        intents = st.session_state.data_processor.get_unique_values('user_intent')
        selected_intents = st.multiselect("用戶意圖", intents, key="intents")

        languages = st.session_state.data_processor.get_unique_values('user_language')
        selected_languages = st.multiselect("語言", languages, key="languages")

        risk_levels = ['安全 (<3s)', '低風險 (3-5s)', '中風險 (5-8s)', '高風險 (>8s)']
        selected_risk_levels = st.multiselect("風險等級", risk_levels, key="risk_levels")

    # Apply filters
    filtered_df = st.session_state.data_processor.filter_data(
        start_date=start_date,
        end_date=end_date,
        min_timecost=timecost_range[0],
        max_timecost=timecost_range[1],
        hotel_names=selected_hotels if selected_hotels else None,
        room_names=selected_rooms if selected_rooms else None,
        user_intents=selected_intents if selected_intents else None,
        user_languages=selected_languages if selected_languages else None,
        risk_levels=selected_risk_levels if selected_risk_levels else None
    )

    # Summary metrics
    metrics = st.session_state.visualizer.create_summary_metrics(filtered_df)

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("總對話數", f"{metrics['total_conversations']:,}")

    with col2:
        st.metric("平均回應時間", f"{metrics['avg_response_time']:.2f}s")

    with col3:
        st.metric("飯店數量", metrics['total_hotels'])

    with col4:
        st.metric("房間數量", metrics['total_rooms'])

    with col5:
        st.metric(
            "高風險對話",
            f"{metrics['high_risk_count']:,}",
            f"{metrics['high_risk_percentage']:.1f}%"
        )

    st.markdown("---")

    # Check if we have data to display
    if filtered_df.empty:
        st.warning("⚠️ 目前篩選條件下無數據，請調整篩選條件")
        return

    # Visualizations
    tab1, tab2, tab3, tab4 = st.tabs(["📊 意圖分佈", "⚠️ 風險分析", "🔑 關鍵實體", "💾 導出數據"])

    with tab1:
        st.subheader("用戶意圖分佈 (User Intent Distribution)")
        intent_fig = st.session_state.visualizer.create_intent_distribution(filtered_df)
        if intent_fig:
            st.plotly_chart(intent_fig, use_container_width=True)
        else:
            st.info("暫無數據")

    with tab2:
        st.subheader("回應時間風險分析 (Response Time Risk Analysis)")
        risk_fig = st.session_state.visualizer.create_response_time_risk_analysis(filtered_df)
        if risk_fig:
            st.plotly_chart(risk_fig, use_container_width=True)

            # Drill-down section
            st.write("---")
            st.write("### 🔍 風險等級詳細分析")
            st.write("選擇風險等級以查看該等級下的意圖分佈")

            risk_level = st.selectbox(
                "選擇風險等級",
                ['安全 (<3s)', '低風險 (3-5s)', '中風險 (5-8s)', '高風險 (>8s)'],
                key="risk_drilldown"
            )

            if risk_level:
                drilldown_fig = st.session_state.visualizer.create_risk_intent_drilldown(filtered_df, risk_level)
                if drilldown_fig:
                    st.plotly_chart(drilldown_fig, use_container_width=True)
                else:
                    st.info(f"該風險等級下暫無數據")
        else:
            st.info("暫無數據")

    with tab3:
        st.subheader("關鍵實體分佈 (Key Entity Distribution)")

        viz_type = st.radio("可視化類型", ["條形圖", "詞雲"], horizontal=True)

        if viz_type == "條形圖":
            entity_fig = st.session_state.visualizer.create_key_entity_distribution(filtered_df)
            if entity_fig:
                st.plotly_chart(entity_fig, use_container_width=True)
            else:
                st.info("暫無數據")
        else:
            wordcloud_img = st.session_state.visualizer.create_wordcloud(filtered_df)
            if wordcloud_img:
                st.image(f"data:image/png;base64,{wordcloud_img}", use_container_width=True)
            else:
                st.info("暫無數據")

    with tab4:
        st.subheader("💾 導出對話紀錄")
        st.write("將當前篩選條件下的對話按住宿時段導出為文字報告")

        col1, col2 = st.columns(2)

        with col1:
            checkin_time = st.time_input(
                "標準入住時間",
                value=datetime.strptime("14:00", "%H:%M").time(),
                key="checkin_time"
            )

        with col2:
            checkout_time = st.time_input(
                "標準退房時間",
                value=datetime.strptime("11:00", "%H:%M").time(),
                key="checkout_time"
            )

        st.write("---")

        if st.button("📥 生成並導出報告", type="primary", use_container_width=True):
            with st.spinner("正在生成報告..."):
                try:
                    content, filename = st.session_state.export_manager.export_to_file(
                        filtered_df,
                        checkin_time.strftime("%H:%M"),
                        checkout_time.strftime("%H:%M")
                    )

                    st.success(f"✅ 報告生成成功！共 {content.count('## 用戶體驗報告')} 個住宿時段")

                    st.download_button(
                        label="⬇️ 下載報告",
                        data=content,
                        file_name=filename,
                        mime="text/plain",
                        use_container_width=True
                    )

                    # Show preview
                    with st.expander("📄 預覽報告內容（前 50 行）"):
                        preview_lines = content.split('\n')[:50]
                        st.text('\n'.join(preview_lines))
                        if len(content.split('\n')) > 50:
                            st.info("... (更多內容請下載完整報告)")

                except Exception as e:
                    st.error(f"❌ 導出失敗：{str(e)}")


def main():
    """Main application entry point"""
    initialize_session_state()

    if not st.session_state.data_loaded:
        upload_page()
    else:
        dashboard_page()


if __name__ == "__main__":
    main()
