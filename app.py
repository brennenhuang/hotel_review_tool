"""
Main Streamlit application for Smart Speaker Conversation Analysis Platform
智能音箱對話分析平台
"""

from datetime import datetime

import streamlit as st

from data_processor import DataProcessor
from export_manager import ExportManager
from visualizations import Visualizer

# Page configuration
st.set_page_config(
    page_title="智能音箱對話分析平台",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
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
""",
    unsafe_allow_html=True,
)


def initialize_session_state():
    """Initialize session state variables"""
    if "data_processor" not in st.session_state:
        st.session_state.data_processor = DataProcessor()
    if "visualizer" not in st.session_state:
        st.session_state.visualizer = Visualizer()
    if "export_manager" not in st.session_state:
        st.session_state.export_manager = ExportManager()
    if "data_loaded" not in st.session_state:
        st.session_state.data_loaded = False
    if "show_drilldown" not in st.session_state:
        st.session_state.show_drilldown = False
    if "selected_risk_level" not in st.session_state:
        st.session_state.selected_risk_level = None


# DEPRECATED: This function is replaced by conversation_upload_page and ui_upload_page
def upload_page():
    """Display upload page (DEPRECATED - use conversation_upload_page instead)"""
    st.markdown(
        '<div class="main-header">🎤 智能音箱對話分析平台</div>', unsafe_allow_html=True
    )
    st.markdown("---")

    st.write("### 📁 數據上傳")
    st.write("上傳包含智能音箱對話紀錄的 CSV 檔案開始分析")

    uploaded_file = st.file_uploader(
        "選擇 CSV 檔案", type=["csv"], help="支援拖曳上傳，最多 100,000 筆數據"
    )

    if uploaded_file is not None:
        with st.spinner("正在處理數據..."):
            success, message = st.session_state.data_processor.load_and_process_csv(
                uploaded_file
            )

            if success:
                st.success(message)
                st.session_state.data_loaded = True
                st.rerun()
            else:
                st.error(message)

    # Show instructions
    with st.expander("📖 使用說明"):
        st.markdown(
            """
        **支援的數據格式：**
        - 檔案格式：CSV
        - 最大筆數：100,000 筆
        - 必需欄位請參考 PRD 文件

        **功能概述：**
        - 📊 多維度數據可視化
        - 🔍 靈活的篩選與查詢
        - ⚠️ 回應時間風險監控
        - 💾 一鍵導出對話報告
        """
        )


def conversation_dashboard_page():
    """Display conversation analysis dashboard page"""
    st.markdown("### 📊 對話分析儀表板")

    # Reset data button
    _, _, col3 = st.columns([6, 1, 1])
    with col3:
        if st.button("🔄 重新上傳", use_container_width=True):
            # Clear all conversation-related session state
            st.session_state.data_loaded = False
            st.session_state.conversation_data_loaded = False
            st.session_state.data_processor = DataProcessor()
            st.session_state.show_drilldown = False

            # Clear filter-related keys to reset widgets
            filter_keys = [
                "date_range", "timecost_range", "hotels", "rooms",
                "intents", "languages", "risk_levels", "risk_drilldown",
                "detail_date_select", "detail_risk_filter"
            ]
            for key in filter_keys:
                if key in st.session_state:
                    del st.session_state[key]

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
                key="date_range",
            )
            start_date = (
                datetime.combine(date_range[0], datetime.min.time())
                if len(date_range) > 0
                else None
            )
            end_date = (
                datetime.combine(date_range[1], datetime.max.time())
                if len(date_range) > 1
                else start_date
            )
        else:
            start_date, end_date = None, None

        # Response timecost filter
        st.subheader("⏱️ 回應耗時 (秒)")
        min_timecost, max_timecost = (
            st.session_state.data_processor.get_timecost_range()
        )
        timecost_range = st.slider(
            "選擇耗時範圍",
            min_value=float(min_timecost),
            max_value=float(min(max_timecost, 20.0)),  # Cap at 20s for better UX
            value=(float(min_timecost), float(min(max_timecost, 20.0))),
            step=0.1,
            key="timecost_range",
        )

        # Categorical filters
        st.subheader("🏨 分類篩選")

        hotels = st.session_state.data_processor.get_unique_values("hotel_name")
        selected_hotels = st.multiselect(
            "飯店名稱", hotels, default=hotels, key="hotels"
        )

        rooms = st.session_state.data_processor.get_unique_values("room_name")
        selected_rooms = st.multiselect("房間號碼", rooms, key="rooms")

        intents = st.session_state.data_processor.get_unique_values("user_intent")
        selected_intents = st.multiselect("用戶意圖", intents, key="intents")

        languages = st.session_state.data_processor.get_unique_values("user_language")
        selected_languages = st.multiselect("語言", languages, key="languages")

        risk_levels = ["安全 (<3s)", "低風險 (3-5s)", "中風險 (5-8s)", "高風險 (>8s)"]
        selected_risk_levels = st.multiselect(
            "風險等級", risk_levels, key="risk_levels"
        )

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
        risk_levels=selected_risk_levels if selected_risk_levels else None,
    )

    # Summary metrics
    metrics = st.session_state.visualizer.create_summary_metrics(filtered_df)

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("總對話數", f"{metrics['total_conversations']:,}")

    with col2:
        st.metric("平均回應時間", f"{metrics['avg_response_time']:.2f}s")

    with col3:
        st.metric("飯店數量", metrics["total_hotels"])

    with col4:
        st.metric("房間數量", metrics["total_rooms"])

    with col5:
        st.metric(
            "高風險對話",
            f"{metrics['high_risk_count']:,}",
            f"{metrics['high_risk_percentage']:.1f}%",
        )

    st.markdown("---")

    # Check if we have data to display
    if filtered_df.empty:
        st.warning("⚠️ 目前篩選條件下無數據，請調整篩選條件")
        return

    # Visualizations
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📊 意圖分佈", "⚠️ 風險分析", "🔑 關鍵實體", "💾 導出數據"]
    )

    with tab1:
        st.subheader("用戶意圖分佈 (User Intent Distribution)")
        intent_fig = st.session_state.visualizer.create_intent_distribution(filtered_df)
        if intent_fig:
            st.plotly_chart(intent_fig, use_container_width=True)
        else:
            st.info("暫無數據")

    with tab2:
        st.subheader("回應時間風險分析 (Response Time Risk Analysis)")
        risk_fig = st.session_state.visualizer.create_response_time_risk_analysis(
            filtered_df
        )
        if risk_fig:
            st.plotly_chart(risk_fig, use_container_width=True)

            # Drill-down section - Intent distribution by risk level
            st.write("---")
            st.write("### 🔍 風險等級詳細分析")
            st.write("選擇風險等級以查看該等級下的意圖分佈")

            risk_level = st.selectbox(
                "選擇風險等級",
                ["安全 (<3s)", "低風險 (3-5s)", "中風險 (5-8s)", "高風險 (>8s)"],
                key="risk_drilldown",
            )

            if risk_level:
                drilldown_fig = (
                    st.session_state.visualizer.create_risk_intent_drilldown(
                        filtered_df, risk_level
                    )
                )
                if drilldown_fig:
                    st.plotly_chart(drilldown_fig, use_container_width=True)
                else:
                    st.info("該風險等級下暫無數據")

            # Detailed conversation table by date and risk level
            st.write("---")
            st.write("### 📋 對話詳細數據查看")
            st.write("選擇日期和風險等級查看具體的對話內容和回應時間")

            # Get available dates from filtered data
            if not filtered_df.empty and 'request_timestamp' in filtered_df.columns:
                available_dates = sorted(
                    filtered_df['request_timestamp'].dt.date.unique()
                )

                col_date, col_risk_filter = st.columns([2, 2])

                with col_date:
                    selected_date = st.selectbox(
                        "選擇日期",
                        options=available_dates,
                        format_func=lambda x: x.strftime('%Y-%m-%d'),
                        key="detail_date_select"
                    )

                with col_risk_filter:
                    risk_filter_option = st.selectbox(
                        "篩選風險等級",
                        options=[
                            "全部風險等級",
                            "安全 (<3s)",
                            "低風險 (3-5s)",
                            "中風險 (5-8s)",
                            "高風險 (>8s)"
                        ],
                        key="detail_risk_filter"
                    )

                if selected_date:
                    # Get selected risk level (None means all levels)
                    selected_risk_for_table = (
                        None if risk_filter_option == "全部風險等級"
                        else risk_filter_option
                    )

                    # Get detailed table
                    detail_table = (
                        st.session_state.visualizer.create_risk_detail_table(
                            filtered_df,
                            selected_date,
                            selected_risk_for_table
                        )
                    )

                    if detail_table is not None and not detail_table.empty:
                        st.write(
                            f"**查看日期：{selected_date.strftime('%Y-%m-%d')}** | "
                            f"**風險等級：{risk_filter_option}** | "
                            f"**共 {len(detail_table)} 筆對話**"
                        )

                        # Display the table with custom styling
                        st.dataframe(
                            detail_table,
                            use_container_width=True,
                            height=400,
                            column_config={
                                "時間戳": st.column_config.DatetimeColumn(
                                    "時間戳",
                                    format="YYYY-MM-DD HH:mm:ss"
                                ),
                                "回應耗時 (秒)": st.column_config.NumberColumn(
                                    "回應耗時 (秒)",
                                    format="%.3f"
                                )
                            }
                        )

                        # Add download button for the detail table
                        csv_data = detail_table.to_csv(index=False).encode('utf-8-sig')
                        st.download_button(
                            label="📥 下載詳細數據 CSV",
                            data=csv_data,
                            file_name=f"risk_detail_{selected_date}_{risk_filter_option}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    else:
                        st.info(
                            f"📊 {selected_date.strftime('%Y-%m-%d')} "
                            f"{risk_filter_option} 無數據"
                        )
        else:
            st.info("暫無數據")

    with tab3:
        st.subheader("關鍵實體分佈 (Key Entity Distribution)")

        viz_type = st.radio("可視化類型", ["條形圖", "詞雲"], horizontal=True)

        if viz_type == "條形圖":
            entity_fig = st.session_state.visualizer.create_key_entity_distribution(
                filtered_df
            )
            if entity_fig:
                st.plotly_chart(entity_fig, use_container_width=True)
            else:
                st.info("暫無數據")
        else:
            wordcloud_img = st.session_state.visualizer.create_wordcloud(filtered_df)
            if wordcloud_img:
                st.image(
                    f"data:image/png;base64,{wordcloud_img}", use_container_width=True
                )
            else:
                st.info("暫無數據")

    with tab4:
        st.subheader("💾 導出對話紀錄")
        st.write("將當前篩選條件下的對話按住宿時段導出為文字報告")

        col1, col2, col3 = st.columns(3)

        with col1:
            checkin_time = st.time_input(
                "標準入住時間",
                value=datetime.strptime("14:00", "%H:%M").time(),
                key="checkin_time",
            )

        with col2:
            checkout_time = st.time_input(
                "標準退房時間",
                value=datetime.strptime("11:00", "%H:%M").time(),
                key="checkout_time",
            )

        with col3:
            # Get available timezones from data processor
            available_timezones = (
                st.session_state.data_processor.get_available_timezones()
            )
            timezone_options = {
                display_name: tz_id for tz_id, display_name in available_timezones
            }

            # 生成動態help文本
            base_help = (
                "選擇報告中顯示的時區。數據原始時區為UTC+8，選擇UTC將轉換為協調世界時。"
            )

            selected_timezone_display = st.selectbox(
                "🌍 選擇時區",
                options=list(timezone_options.keys()),
                index=0,  # Default to first option (UTC)
                key="target_timezone",
                help=base_help,
            )

            selected_timezone = timezone_options[selected_timezone_display]

            # 檢查是否為有夏令時的時區
            has_dst = selected_timezone in [
                "America/New_York",
                "America/Los_Angeles",
                "Europe/London",
            ]

            # 添加夏令時強制選擇選項（僅對有夏令時的時區顯示）
            dst_override = None
            if has_dst:
                dst_override = st.radio(
                    "⏰ 時間模式",
                    options=["自動", "強制夏令時", "強制標準時間"],
                    index=0,
                    key="dst_override",
                    help="自動：根據當前日期判斷；強制：手動指定使用夏令時還是標準時間",
                    horizontal=True,
                )

            # 顯示當前選擇時區的狀態信息
            timezone_status = st.session_state.data_processor.get_timezone_info(
                selected_timezone, dst_override
            )
            if timezone_status:
                st.caption(f"⏰ **時區狀態:** {timezone_status.strip()}")

        # Show timezone info if different timezone is selected
        if selected_timezone != "Asia/Taipei" and st.session_state.data_loaded:
            with st.expander("🌍 時區說明", expanded=True):
                st.info("📋 **時區轉換說明:**")
                st.write("• 🏨 **入住/退房時間**: 保持酒店當地時間不變")
                st.write("• 📊 **對話時間戳**: 轉換為所選時區顯示")
                st.write("• 🔄 **住宿時段劃分**: 系統自動處理時區對應關係")

                col_local, col_target = st.columns(2)
                with col_local:
                    st.success(
                        f"🏨 當地時間 (UTC+8)\n入住: {checkin_time.strftime('%H:%M')} | 退房: {checkout_time.strftime('%H:%M')}"
                    )
                with col_target:
                    st.info(
                        f"📊 報告時區 ({selected_timezone_display})\n對話時間戳將轉換顯示"
                    )

        st.write("---")

        if st.button("📥 生成並導出報告", type="primary", use_container_width=True):
            with st.spinner("正在生成報告..."):
                try:
                    # Convert timezone if needed
                    if selected_timezone != "Asia/Taipei":
                        # Need timezone conversion for data
                        converted_df = st.session_state.data_processor.convert_timezone(
                            source_timezone="Asia/Taipei",  # Original data timezone (UTC+8)
                            target_timezone=selected_timezone,
                            dst_override=dst_override,
                        )
                        if converted_df is not None:
                            export_df = converted_df
                        else:
                            export_df = filtered_df
                            st.warning("時區轉換失敗，使用原始時區數據")
                    else:
                        export_df = filtered_df

                    # Keep check-in/check-out times as local hotel times
                    checkin_str = checkin_time.strftime("%H:%M")
                    checkout_str = checkout_time.strftime("%H:%M")

                    content, filename = st.session_state.export_manager.export_to_file(
                        export_df,
                        checkin_str,
                        checkout_str,
                        target_timezone=selected_timezone,
                    )

                    st.success(
                        f"✅ 報告生成成功！共 {content.count('## 用戶體驗報告')} 個住宿時段"
                    )

                    st.download_button(
                        label="⬇️ 下載報告",
                        data=content,
                        file_name=filename,
                        mime="text/plain",
                        use_container_width=True,
                    )

                    # Show preview
                    with st.expander("📄 預覽報告內容（前 50 行）"):
                        preview_lines = content.split("\n")[:50]
                        st.text("\n".join(preview_lines))
                        if len(content.split("\n")) > 50:
                            st.info("... (更多內容請下載完整報告)")

                except Exception as e:
                    st.error(f"❌ 導出失敗：{str(e)}")


def main():
    """Main application entry point"""
    initialize_session_state()

    # Sidebar navigation
    with st.sidebar:
        st.title("🎤 分析平台")
        page = st.selectbox(
            "選擇分析模組", ["💬 對話分析", "📱 UI行為分析"], key="page_selection"
        )

        st.markdown("---")

    # Route to different pages based on selection
    if page == "💬 對話分析":
        conversation_analysis_page()
    elif page == "📱 UI行為分析":
        ui_behavior_analysis_page()


def conversation_analysis_page():
    """Conversation analysis page (original functionality)"""
    st.markdown(
        '<h1 class="main-header">💬 智能音箱對話分析</h1>', unsafe_allow_html=True
    )

    if not st.session_state.get("conversation_data_loaded", False):
        conversation_upload_page()
    else:
        conversation_dashboard_page()


def ui_behavior_analysis_page():
    """UI behavior analysis page (new functionality)"""
    st.markdown(
        '<h1 class="main-header">📱 智能音箱UI行為分析</h1>', unsafe_allow_html=True
    )

    if not st.session_state.get("ui_data_loaded", False):
        ui_upload_page()
    else:
        ui_dashboard_page()


def conversation_upload_page():
    """Original upload page renamed"""
    st.markdown(
        """
        <div style="text-align: center; padding: 2rem;">
            <h2>🎤 歡迎使用智能音箱對話分析平台</h2>
            <p style="font-size: 1.1rem; color: #666;">
                上傳您的對話數據CSV檔案，開始進行深度分析
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 📁 數據上傳")

    # File upload
    uploaded_file = st.file_uploader(
        "選擇CSV檔案", type=["csv"], help="僅支援CSV格式，數據筆數限制：100,000筆以內"
    )

    if uploaded_file is not None:
        try:
            with st.spinner("正在處理數據..."):
                # Initialize data processor if not exists
                if "data_processor" not in st.session_state:
                    st.session_state.data_processor = DataProcessor()
                if "visualizer" not in st.session_state:
                    st.session_state.visualizer = Visualizer()
                if "export_manager" not in st.session_state:
                    st.session_state.export_manager = ExportManager()

                # Load and process data
                success, message = (
                    st.session_state.data_processor.load_and_process_csv(
                        uploaded_file
                    )
                )

                if success:
                    st.session_state.conversation_data_loaded = True
                    st.session_state.data_loaded = (
                        True  # Keep for backward compatibility
                    )
                    st.success(f"✅ {message}")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")

        except Exception as e:
            st.error(f"❌ 處理過程中發生錯誤：{str(e)}")


def ui_upload_page():
    """UI behavior data upload page"""
    st.markdown(
        """
        <div style="text-align: center; padding: 2rem;">
            <h2>📱 UI介面行為分析</h2>
            <p style="font-size: 1.1rem; color: #666;">
                上傳您的UI行為數據CSV檔案，分析用戶互動模式
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 📁 數據上傳")

    # File upload
    uploaded_file = st.file_uploader(
        "選擇UI行為CSV檔案",
        type=["csv"],
        help="僅支援CSV格式，數據筆數限制：100,000筆以內",
        key="ui_file_uploader",
    )

    if uploaded_file is not None:
        try:
            with st.spinner("正在處理UI行為數據..."):
                # Initialize SPOT data processor
                from spot_data_processor import SpotDataProcessor
                from spot_visualizations import SpotVisualizer

                if "spot_data_processor" not in st.session_state:
                    st.session_state.spot_data_processor = SpotDataProcessor()
                if "spot_visualizer" not in st.session_state:
                    st.session_state.spot_visualizer = SpotVisualizer()

                # Load and process UI behavior data
                success = st.session_state.spot_data_processor.load_data(uploaded_file)

                if success:
                    st.session_state.ui_data_loaded = True
                    st.success("✅ UI行為數據載入成功！")
                    st.rerun()
                else:
                    st.error("❌ UI行為數據載入失敗，請檢查檔案格式")

        except Exception as e:
            st.error(f"❌ 處理過程中發生錯誤：{str(e)}")


def ui_dashboard_page():
    """UI behavior analysis dashboard"""
    st.markdown("### 📊 UI行為分析儀表板")

    # Reset data button
    col1, col2, col3 = st.columns([6, 1, 1])
    with col3:
        if st.button("🔄 重新上傳", use_container_width=True, key="ui_reset_button"):
            st.session_state.ui_data_loaded = False
            if "spot_data_processor" in st.session_state:
                del st.session_state.spot_data_processor
            if "spot_visualizer" in st.session_state:
                del st.session_state.spot_visualizer
            st.rerun()

    st.markdown("---")

    # Sidebar filters
    with st.sidebar:
        st.header("🔍 全域篩選器")
        st.write("選擇篩選條件以過濾整個儀表板的數據")

        # Get filter options
        filter_options = st.session_state.spot_data_processor.get_filter_options()

        # Hotel filter
        st.subheader("🏨 飯店")
        selected_hotels = st.multiselect(
            "選擇飯店",
            options=filter_options["hotels"],
            default=(
                filter_options["hotels"][:3]
                if len(filter_options["hotels"]) > 3
                else filter_options["hotels"]
            ),
            key="ui_hotel_filter",
        )

        # Room filter
        st.subheader("📍 房間")
        selected_rooms = st.multiselect(
            "選擇房間",
            options=filter_options["rooms"],
            default=(
                filter_options["rooms"][:5]
                if len(filter_options["rooms"]) > 5
                else filter_options["rooms"]
            ),
            key="ui_room_filter",
        )

        # Device filter
        st.subheader("📱 設備")
        selected_devices = st.multiselect(
            "選擇設備ID",
            options=filter_options["devices"],
            default=(
                filter_options["devices"][:5]
                if len(filter_options["devices"]) > 5
                else filter_options["devices"]
            ),
            key="ui_device_filter",
        )

        # Interaction filter
        st.subheader("💆 互動方式")
        selected_interactions = st.multiselect(
            "選擇互動方式",
            options=filter_options["interactions"],
            default=filter_options["interactions"],
            key="ui_interaction_filter",
        )

        # Intent filter
        st.subheader("🎯 意圖")
        selected_intents = st.multiselect(
            "選擇用戶意圖",
            options=filter_options["intents"],
            default=(
                filter_options["intents"][:10]
                if len(filter_options["intents"]) > 10
                else filter_options["intents"]
            ),
            key="ui_intent_filter",
        )

        # Chart selection and font size controls
        st.markdown("---")
        st.subheader("📊 圓餅圖選擇與設定")

        # Chart type selection
        chart_options = {
            "原始互動方式分佈": "raw_interaction",
            "融合互動方式分佈": "merged_interaction",
            "用戶意圖分佈": "intent_distribution",
            "其他意圖詳細分佈": "others_breakdown",
        }

        col_select, col_font = st.columns([2, 1])

        with col_select:
            selected_chart_name = st.selectbox(
                "選擇要顯示的圓餅圖",
                options=list(chart_options.keys()),
                index=2,  # 預設選擇"用戶意圖分佈"
                key="selected_chart_type",
                help="選擇要在下方顯示的圓餅圖類型",
            )
            selected_chart_type = chart_options[selected_chart_name]

        with col_font:
            # 根據選中的圖表類型設定預設字體大小
            default_font_sizes = {
                "raw_interaction": 12,
                "merged_interaction": 12,
                "intent_distribution": 15,
                "others_breakdown": 12,
            }

            font_size = st.number_input(
                "字體大小",
                min_value=8,
                max_value=24,
                value=default_font_sizes[selected_chart_type],
                step=1,
                key=f"{selected_chart_type}_font_size",
                help=f"調整{selected_chart_name}圓餅圖的字體大小",
            )

    # Get filtered data
    filtered_df = st.session_state.spot_data_processor.get_filtered_data(
        hotel_filter=selected_hotels,
        room_filter=selected_rooms,
        device_filter=selected_devices,
        interaction_filter=selected_interactions,
        intent_filter=selected_intents,
    )

    if filtered_df.empty:
        st.warning("⚠️ 當前篩選條件下無數據，請調整篩選條件")
        return

    # Display summary metrics
    summary_stats = st.session_state.spot_data_processor.get_summary_stats(filtered_df)
    st.session_state.spot_visualizer.display_summary_metrics(summary_stats)

    st.markdown("---")

    # Display selected chart
    st.subheader(f"📊 {selected_chart_name}")

    # Prepare data based on chart type
    if selected_chart_type in ["raw_interaction", "merged_interaction"]:
        interaction_data = (
            st.session_state.spot_data_processor.get_interaction_distribution(
                filtered_df
            )
        )
    elif selected_chart_type in ["intent_distribution", "others_breakdown"]:
        intent_data = st.session_state.spot_data_processor.get_intent_distribution(
            filtered_df, merge_small=True, threshold=1.0
        )

    # Create and display the selected chart
    if selected_chart_type == "raw_interaction":
        chart = st.session_state.spot_visualizer.create_raw_interaction_pie_chart(
            interaction_data["raw"], font_size
        )
        st.plotly_chart(chart, use_container_width=True)

    elif selected_chart_type == "merged_interaction":
        chart = st.session_state.spot_visualizer.create_merged_interaction_pie_chart(
            interaction_data["merged"], font_size
        )
        st.plotly_chart(chart, use_container_width=True)

    elif selected_chart_type == "intent_distribution":
        chart = st.session_state.spot_visualizer.create_intent_distribution_pie_chart(
            intent_data.get("distribution", {}), font_size
        )
        st.plotly_chart(chart, use_container_width=True)

    elif selected_chart_type == "others_breakdown":
        others_breakdown = intent_data.get("others_breakdown", {})
        if others_breakdown:
            chart = st.session_state.spot_visualizer.create_others_breakdown_pie_chart(
                others_breakdown, font_size
            )
            st.plotly_chart(chart, use_container_width=True)
        else:
            st.info("📊 所有意圖占比均 ≥ 1%，無需顯示詳細分佈")
            st.markdown(
                """
            **說明：** 當前數據中沒有小於1%的意圖項目需要單獨顯示。
            您可以選擇「用戶意圖分佈」查看完整的意圖分析。
            """
            )

    st.markdown("---")

    # MODULE_NOT_SUPPORT details table
    error_df = st.session_state.spot_data_processor.get_module_not_support_details(
        filtered_df
    )
    st.session_state.spot_visualizer.display_module_not_support_table(error_df)


if __name__ == "__main__":
    main()
