"""
SPOT Visualizations for Smart Speaker UI Behavior Analysis
智慧音箱UI介面行為分析可視化模組
"""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import pandas as pd
from typing import Dict


class SpotVisualizer:
    """智慧音箱UI行為數據可視化類別"""

    def __init__(self):
        """初始化可視化器"""
        # 為不同類型的圓餅圖設計獨特的色彩方案
        self.color_schemes = {
            # 原始互動方式 - 深藍色調系列
            "raw_interaction": {
                "UI": "#1f77b4",  # 藍色
                "HARDWARE": "#ff7f0e",  # 橙色
                "SYSTEM": "#2ca02c",  # 綠色
                "VOICE": "#d62728",  # 紅色
            },
            # 融合互動方式 - 暖色調系列
            "merged_interaction": {
                "UI + SYSTEM": "#aec7e8",  # 淺藍色
                "HARDWARE": "#ffbb78",  # 淺橙色
                "VOICE": "#ff9896",  # 淺紅色
            },
            # 用戶意圖分佈 - 綠色調系列 + 特殊意圖色彩
            "intent_distribution": [
                "#1f77b4",  # 藍色
                "#aec7e8",  # 淺藍色
                "#ff7f0e",  # 橙色
                "#ffbb78",  # 淺橙色
                "#2ca02c",  # 綠色
                "#98df8a",  # 淺綠色
                "#d62728",  # 紅色
                "#ff9896",  # 淺紅色
                "#9467bd",  # 紫色
                "#c5b0d5",  # 淺紫色
                "#8c564b",  # 棕色
                "#c49c94",  # 淺棕色
                "#e377c2",  # 粉紅色
                "#f7b6d2",  # 淺粉紅色
                "#7f7f7f",  # 灰色
                "#bcbd22",  # 黃綠色
                "#17becf",  # 青色
                "#9edae5",  # 淺青色
            ],
            # 其他意圖詳細分佈 - 使用與 intent_distribution 相同的色彩方案
            "others_breakdown": [
                "#1f77b4",  # 藍色
                "#aec7e8",  # 淺藍色
                "#ff7f0e",  # 橙色
                "#ffbb78",  # 淺橙色
                "#2ca02c",  # 綠色
                "#98df8a",  # 淺綠色
                "#d62728",  # 紅色
                "#ff9896",  # 淺紅色
                "#9467bd",  # 紫色
                "#c5b0d5",  # 淺紫色
                "#8c564b",  # 棕色
                "#c49c94",  # 淺棕色
                "#e377c2",  # 粉紅色
                "#f7b6d2",  # 淺粉紅色
                "#7f7f7f",  # 灰色
                "#bcbd22",  # 黃綠色
                "#17becf",  # 青色
                "#9edae5",  # 淺青色
            ],
        }

        # 特殊意圖的固定顏色
        self.special_colors = {
            "MODULE_NOT_SUPPORT": "#c0392b",  # 深紅色 - 錯誤
            "LOCALE": "#e67e22",  # 深橙色 - 語言設定
            "WAKE UP": "#229954",  # 深綠色 - 喚醒功能
        }

    def _calculate_dynamic_layout(
        self, font_size: int, base_height: int = 400, data_count: int = 0
    ) -> Dict:
        """
        根據字體大小和數據數量計算動態佈局參數

        Args:
            font_size: 字體大小
            base_height: 基礎高度
            data_count: 數據項目數量

        Returns:
            Dict: 包含 margin, height 和 text_strategy 的佈局參數
        """
        # 根據字體大小調整邊距（字體越大，邊距越大）
        margin_factor = max(1.5, font_size / 8.0)  # 更激進的邊距調整
        base_margin = 40  # 增加基礎邊距

        # 根據數據項目數量調整邊距（項目越多，需要越多空間）
        data_factor = max(1.2, data_count / 6.0) if data_count > 0 else 1.0

        dynamic_margin = {
            "t": int(100 * margin_factor),  # 頂部邊距大幅增加
            "b": int(base_margin * margin_factor * data_factor),  # 底部邊距
            "l": int(base_margin * margin_factor * data_factor),  # 左側邊距
            "r": int(
                base_margin * margin_factor * data_factor * 3
            ),  # 右側邊距大幅增加（外部文字需要更多空間）
        }

        # 根據字體大小和數據數量調整高度
        height_factor = max(1.3, font_size / 10.0)
        data_height_factor = max(1.1, data_count / 8.0) if data_count > 0 else 1.0
        dynamic_height = int(base_height * height_factor * data_height_factor)

        # 決定文字顯示策略
        text_strategy = self._determine_text_strategy(font_size, data_count)

        return {
            "margin": dynamic_margin,
            "height": dynamic_height,
            "text_strategy": text_strategy,
        }

    def _determine_text_strategy(self, font_size: int, data_count: int) -> Dict:
        """
        根據字體大小和數據數量決定文字顯示策略

        Args:
            font_size: 字體大小
            data_count: 數據項目數量

        Returns:
            Dict: 文字顯示策略配置
        """
        strategy = {
            "position": "auto",
            "min_percentage": 0,  # 最小顯示百分比閾值
            "show_all": True,
        }

        # 大字體或項目太多時，使用更保守的顯示策略
        if font_size >= 18 or data_count >= 12:
            strategy.update(
                {
                    "position": "outside",  # 強制外部顯示
                    "min_percentage": (
                        1.5 if data_count >= 15 else 1.0
                    ),  # 設置最小顯示閾值
                    "show_all": False,
                }
            )
        elif font_size >= 14 or data_count >= 8:
            strategy.update(
                {"position": "outside", "min_percentage": 0.8, "show_all": False}
            )

        return strategy

    def _apply_text_strategy(self, labels, values, strategy: Dict):
        """
        根據策略過濾和調整文字顯示

        Args:
            labels: 標籤列表
            values: 數值列表
            strategy: 文字顯示策略

        Returns:
            Tuple: (filtered_labels, filtered_values, text_info)
        """
        if strategy["show_all"]:
            return labels, values, "label+percent+value"

        # 計算百分比並過濾小比例項目
        total = sum(values)
        min_threshold = strategy["min_percentage"]

        filtered_labels = []
        filtered_values = []
        hidden_count = 0
        hidden_total = 0

        for label, value in zip(labels, values):
            percentage = (value / total) * 100 if total > 0 else 0
            if percentage >= min_threshold:
                filtered_labels.append(label)
                filtered_values.append(value)
            else:
                hidden_count += 1
                hidden_total += value

        # 如果有隱藏項目，添加到"其他"或合併
        if hidden_count > 0:
            if "其他" in filtered_labels:
                # 如果已經有"其他"類別，合併數值
                other_index = filtered_labels.index("其他")
                filtered_values[other_index] += hidden_total
            else:
                # 添加新的"其他"類別
                filtered_labels.append(f"其他 ({hidden_count}項)")
                filtered_values.append(hidden_total)

        return filtered_labels, filtered_values, "label+percent+value"

    def create_raw_interaction_pie_chart(
        self, distribution_data: Dict, font_size: int = 12
    ) -> go.Figure:
        """
        創建原始互動方式分佈圓餅圖

        Args:
            distribution_data: 互動方式分佈數據
            font_size: 圓餅圖字體大小，預設為12

        Returns:
            go.Figure: Plotly圖表物件
        """
        if not distribution_data:
            # 空數據的情況
            fig = go.Figure()
            fig.add_annotation(
                text="暫無數據",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=16),
            )
            fig.update_layout(title="原始互動方式分佈", showlegend=False, height=400)
            return fig

        # 準備數據
        labels = list(distribution_data.keys())
        values = list(distribution_data.values())
        total = sum(values)

        # 計算百分比
        percentages = [(v / total * 100) if total > 0 else 0 for v in values]

        # 創建標籤文字（包含數量和百分比）
        hover_text = [
            f"{label}<br>數量: {value:,}<br>比例: {pct:.1f}%"
            for label, value, pct in zip(labels, values, percentages)
        ]

        # 使用原始互動方式專用色彩方案（藍色調系列）
        color_scheme = self.color_schemes["raw_interaction"]
        colors = [color_scheme.get(label, "#34495e") for label in labels]

        # 計算動態佈局參數
        data_count = len(distribution_data) if distribution_data else 0
        layout_params = self._calculate_dynamic_layout(font_size, 400, data_count)

        # 創建圓餅圖
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=labels,
                    values=values,
                    hovertext=hover_text,
                    hovertemplate="%{hovertext}<extra></extra>",
                    textinfo="label+percent+value",
                    texttemplate="%{label}<br>%{value:,}<br>(%{percent})",
                    textposition="auto",  # 自動選擇文字位置避免溢出
                    marker=dict(colors=colors, line=dict(color="white", width=2)),
                    pull=[
                        0.05 if label == "VOICE" else 0 for label in labels
                    ],  # 突出顯示語音互動
                )
            ]
        )

        fig.update_layout(
            title={
                "text": "🎯 原始互動方式分佈",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 18, "family": "Arial, sans-serif"},
            },
            font=dict(size=font_size),
            height=layout_params["height"],
            margin=layout_params["margin"],
            showlegend=True,
            legend=dict(
                orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02
            ),
        )

        return fig

    def create_merged_interaction_pie_chart(
        self, distribution_data: Dict, font_size: int = 12
    ) -> go.Figure:
        """
        創建融合互動方式分佈圓餅圖

        Args:
            distribution_data: 融合後的互動方式分佈數據
            font_size: 圓餅圖字體大小，預設為12

        Returns:
            go.Figure: Plotly圖表物件
        """
        if not distribution_data:
            # 空數據的情況
            fig = go.Figure()
            fig.add_annotation(
                text="暫無數據",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=16),
            )
            fig.update_layout(title="融合互動方式分佈", showlegend=False, height=400)
            return fig

        # 準備數據
        labels = list(distribution_data.keys())
        values = list(distribution_data.values())
        total = sum(values)

        # 計算百分比
        percentages = [(v / total * 100) if total > 0 else 0 for v in values]

        # 創建標籤文字
        hover_text = [
            f"{label}<br>數量: {value:,}<br>比例: {pct:.1f}%"
            for label, value, pct in zip(labels, values, percentages)
        ]

        # 使用融合互動方式專用色彩方案（暖色調系列）
        color_scheme = self.color_schemes["merged_interaction"]
        colors = [color_scheme.get(label, "#7f8c8d") for label in labels]

        # 計算動態佈局參數
        data_count = len(distribution_data) if distribution_data else 0
        layout_params = self._calculate_dynamic_layout(font_size, 400, data_count)

        # 創建圓餅圖
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=labels,
                    values=values,
                    hovertext=hover_text,
                    hovertemplate="%{hovertext}<extra></extra>",
                    textinfo="label+percent+value",
                    texttemplate="%{label}<br>%{value:,}<br>(%{percent})",
                    textposition="auto",  # 自動選擇文字位置避免溢出
                    marker=dict(colors=colors, line=dict(color="white", width=2)),
                    pull=[
                        0.05 if label == "VOICE" else 0 for label in labels
                    ],  # 突出顯示語音互動
                )
            ]
        )

        fig.update_layout(
            title={
                "text": "🔀 融合互動方式分佈",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 18, "family": "Arial, sans-serif"},
            },
            font=dict(size=font_size),
            height=layout_params["height"],
            margin=layout_params["margin"],
            showlegend=True,
            legend=dict(
                orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02
            ),
        )

        return fig

    def create_intent_distribution_pie_chart(
        self, intent_data: Dict, font_size: int = 15
    ) -> go.Figure:
        """
        創建用戶意圖分佈圓餅圖

        Args:
            intent_data: 用戶意圖分佈數據
            font_size: 圓餅圖字體大小，預設為15

        Returns:
            go.Figure: Plotly圖表物件
        """
        if not intent_data:
            # 空數據的情況
            fig = go.Figure()
            fig.add_annotation(
                text="暫無數據",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=16),
            )
            fig.update_layout(title="用戶意圖分佈", showlegend=False, height=500)
            return fig

        # 準備數據
        labels = list(intent_data.keys())
        values = list(intent_data.values())
        data_count = len(labels)

        # 計算動態佈局參數（用戶意圖圖較高，考慮數據項目數量）
        layout_params = self._calculate_dynamic_layout(font_size, 500, data_count)
        text_strategy = layout_params["text_strategy"]

        # 根據策略過濾數據（如果字體太大或項目太多）
        filtered_labels, filtered_values, text_info = self._apply_text_strategy(
            labels, values, text_strategy
        )

        # 重新計算基於過濾後的數據
        total = sum(filtered_values)
        percentages = [(v / total * 100) if total > 0 else 0 for v in filtered_values]

        # 創建標籤文字
        hover_text = [
            f"{label}<br>數量: {value:,}<br>比例: {pct:.1f}%"
            for label, value, pct in zip(filtered_labels, filtered_values, percentages)
        ]

        # 特殊意圖高亮顯示
        special_intents = {"LOCALE", "WAKE UP", "MODULE_NOT_SUPPORT"}
        pull_values = [
            0.1 if label in special_intents else 0 for label in filtered_labels
        ]

        # 使用用戶意圖分佈專用色彩方案（綠色調系列）
        colors = []
        intent_colors = self.color_schemes["intent_distribution"]
        color_index = 0

        for label in filtered_labels:
            if label in self.special_colors:
                # 特殊意圖使用固定顏色
                colors.append(self.special_colors[label])
            elif "其他" in label:
                colors.append("#95a5a6")  # 灰色 - 其他項目
            else:
                # 普通意圖使用綠色調系列
                colors.append(intent_colors[color_index % len(intent_colors)])
                color_index += 1

        # 創建圓餅圖
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=filtered_labels,
                    values=filtered_values,
                    hovertext=hover_text,
                    hovertemplate="%{hovertext}<extra></extra>",
                    textinfo=text_info,
                    texttemplate="%{label}<br>%{value:,}<br>(%{percent})",
                    textposition=text_strategy["position"],  # 使用策略決定的位置
                    marker=dict(colors=colors, line=dict(color="white", width=2)),
                    pull=pull_values,
                )
            ]
        )

        fig.update_layout(
            title={
                "text": "🎯 用戶意圖分佈",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 18, "family": "Arial, sans-serif"},
            },
            font=dict(size=font_size),
            height=layout_params["height"],
            margin=layout_params["margin"],
            showlegend=True,
            legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
        )

        return fig

    def create_others_breakdown_pie_chart(
        self, others_data: Dict, font_size: int = 12
    ) -> go.Figure:
        """
        創建"其他"意圖詳細分佈圓餅圖

        Args:
            others_data: "其他"意圖的詳細分佈數據
            font_size: 圓餅圖字體大小，預設為12

        Returns:
            go.Figure: Plotly圖表物件
        """
        if not others_data:
            # 空數據的情況
            fig = go.Figure()
            fig.add_annotation(
                text='無"其他"意圖數據',
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=16),
            )
            fig.update_layout(title='"其他"意圖詳細分佈', showlegend=False, height=400)
            return fig

        # 準備數據
        labels = list(others_data.keys())
        values = list(others_data.values())
        total = sum(values)

        # 計算百分比
        percentages = [(v / total * 100) if total > 0 else 0 for v in values]

        # 創建標籤文字
        hover_text = [
            f"{label}<br>數量: {value:,}<br>比例: {pct:.2f}%"
            for label, value, pct in zip(labels, values, percentages)
        ]

        # 使用其他意圖詳細分佈專用色彩方案（紫色調系列）
        others_colors = self.color_schemes["others_breakdown"]
        chart_colors = others_colors[: len(labels)]

        # 計算動態佈局參數
        data_count = len(others_data) if others_data else 0
        layout_params = self._calculate_dynamic_layout(font_size, 400, data_count)

        # 創建圓餅圖
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=labels,
                    values=values,
                    hovertext=hover_text,
                    hovertemplate="%{hovertext}<extra></extra>",
                    textinfo="label+percent+value",
                    texttemplate="%{label}<br>%{value:,}<br>(%{percent})",
                    textposition="auto",  # 自動選擇文字位置避免溢出
                    marker=dict(colors=chart_colors, line=dict(color="white", width=2)),
                    textfont=dict(
                        size=max(8, font_size - 2)
                    ),  # 略小於主圓餅圖，但不小於8
                )
            ]
        )

        fig.update_layout(
            title={
                "text": "📊 其他意圖詳細分佈 (< 1%)",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 16, "family": "Arial, sans-serif"},
            },
            font=dict(size=font_size),
            height=layout_params["height"],
            margin=layout_params["margin"],
            showlegend=True,
            legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
        )

        return fig

    def display_module_not_support_table(self, error_df: pd.DataFrame):
        """
        顯示MODULE_NOT_SUPPORT錯誤詳情表格

        Args:
            error_df: 包含錯誤詳情的數據框
        """
        st.subheader("🚨 系統錯誤詳情 (MODULE_NOT_SUPPORT)")

        if error_df.empty:
            st.info("✅ 當前篩選條件下無系統錯誤記錄")
            return

        st.warning(f"⚠️ 發現 {len(error_df)} 筆系統錯誤記錄")

        # 顯示表格
        st.dataframe(
            error_df, use_container_width=True, height=min(400, len(error_df) * 35 + 50)
        )

        # 提供下載功能
        if not error_df.empty:
            csv = error_df.to_csv(index=False)
            st.download_button(
                label="📥 下載錯誤詳情 (CSV)",
                data=csv,
                file_name=f"module_not_support_errors_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )

    def display_summary_metrics(self, summary_stats: Dict):
        """
        顯示統計摘要指標卡片

        Args:
            summary_stats: 統計摘要數據
        """
        st.subheader("📊 統計摘要")

        # 創建指標卡片
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="總互動次數",
                value=f"{summary_stats.get('total_interactions', 0):,}",
                delta=None,
            )

        with col2:
            st.metric(
                label="活躍設備數",
                value=f"{summary_stats.get('active_devices', 0):,}",
                delta=None,
            )

        with col3:
            error_rate = summary_stats.get("error_rate", 0)
            st.metric(
                label="錯誤率",
                value=f"{error_rate:.1f}%",
                delta=None,
                delta_color="inverse",  # 錯誤率越低越好
            )

        with col4:
            top_rooms = summary_stats.get("top_rooms", [])
            if top_rooms:
                top_room = top_rooms[0]
                st.metric(
                    label="最活躍房間",
                    value=top_room["room"],
                    delta=f"{top_room['count']} 次互動",
                )
            else:
                st.metric(label="最活躍房間", value="無數據", delta=None)

        # 顯示最活躍房間詳情
        if top_rooms and len(top_rooms) > 1:
            with st.expander("🏆 最活躍房間 Top 5"):
                for i, room_info in enumerate(top_rooms, 1):
                    st.write(
                        f"{i}. **{room_info['room']}** - {room_info['count']:,} 次互動"
                    )

    def create_interaction_trend_chart(self, df: pd.DataFrame) -> go.Figure:
        """
        創建互動趨勢圖（如果有時間戳數據）

        Args:
            df: 包含時間戳的數據框

        Returns:
            go.Figure: Plotly圖表物件
        """
        # 這是一個可選功能，如果有時間戳數據可以顯示趨勢
        if df.empty or "timestamp" not in df.columns:
            return None

        # 按小時統計互動次數
        df_time = df.copy()
        df_time["hour"] = pd.to_datetime(df_time["timestamp"]).dt.hour
        hourly_counts = (
            df_time.groupby(["hour", "interaction"]).size().reset_index(name="count")
        )

        # 創建堆疊柱狀圖
        fig = px.bar(
            hourly_counts,
            x="hour",
            y="count",
            color="interaction",
            title="📈 每小時互動趨勢",
            labels={"hour": "小時", "count": "互動次數"},
            color_discrete_map={
                "UI": "#1f77b4",
                "HARDWARE": "#ff7f0e",
                "SYSTEM": "#2ca02c",
                "VOICE": "#d62728",
            },
        )

        fig.update_layout(
            height=400,
            xaxis_title="小時 (0-23)",
            yaxis_title="互動次數",
            showlegend=True,
        )

        return fig
