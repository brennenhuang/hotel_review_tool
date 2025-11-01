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
        self.color_palette = [
            "#1f77b4",
            "#ff7f0e",
            "#2ca02c",
            "#d62728",
            "#9467bd",
            "#8c564b",
            "#e377c2",
            "#7f7f7f",
            "#bcbd22",
            "#17becf",
        ]

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

        # 自定義顏色映射
        color_mapping = {
            "UI": "#1f77b4",
            "HARDWARE": "#ff7f0e",
            "SYSTEM": "#2ca02c",
            "VOICE": "#d62728",
        }
        colors = [color_mapping.get(label, "#gray") for label in labels]

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
            height=400,
            margin=dict(t=60, b=20, l=20, r=20),
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

        # 自定義顏色映射
        color_mapping = {
            "UI + SYSTEM": "#9467bd",
            "HARDWARE": "#ff7f0e",
            "VOICE": "#d62728",
        }
        colors = [color_mapping.get(label, "#gray") for label in labels]

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
            height=400,
            margin=dict(t=60, b=20, l=20, r=20),
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
        total = sum(values)

        # 計算百分比
        percentages = [(v / total * 100) if total > 0 else 0 for v in values]

        # 創建標籤文字
        hover_text = [
            f"{label}<br>數量: {value:,}<br>比例: {pct:.1f}%"
            for label, value, pct in zip(labels, values, percentages)
        ]

        # 特殊意圖高亮顯示
        special_intents = {"LOCALE", "WAKE UP", "MODULE_NOT_SUPPORT"}
        pull_values = [0.1 if label in special_intents else 0 for label in labels]

        # 為特殊意圖分配特定顏色
        colors = []
        for i, label in enumerate(labels):
            if label == "MODULE_NOT_SUPPORT":
                colors.append("#d62728")  # 紅色 - 錯誤
            elif label == "LOCALE":
                colors.append("#ff7f0e")  # 橙色 - 語言設定
            elif label == "WAKE UP":
                colors.append("#2ca02c")  # 綠色 - 喚醒功能
            else:
                colors.append(self.color_palette[i % len(self.color_palette)])

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
            height=500,
            margin=dict(t=60, b=20, l=20, r=20),
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

        # 使用較淺的顏色調色盤來表示這是"其他"類別
        colors = [
            "#FFB6C1",
            "#FFC0CB",
            "#FFE4E1",
            "#F0E68C",
            "#E6E6FA",
            "#DDA0DD",
            "#F5DEB3",
            "#D3D3D3",
            "#B0E0E6",
            "#AFEEEE",
        ]
        chart_colors = colors[: len(labels)]

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
                    marker=dict(colors=chart_colors, line=dict(color="white", width=2)),
                    textfont=dict(size=font_size - 2),  # 略小於主圓餅圖
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
            height=400,
            margin=dict(t=60, b=20, l=20, r=20),
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
