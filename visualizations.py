"""
Visualization module for Smart Speaker Conversation Analysis Platform
Handles all chart generation using Plotly
"""

import base64
import io
from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud


class Visualizer:
    """Create visualizations for conversation data"""

    @staticmethod
    def create_intent_distribution(df: pd.DataFrame) -> Optional[go.Figure]:
        """
        Create intent distribution pie chart

        Args:
            df: Filtered DataFrame

        Returns:
            Plotly figure or None if no data
        """
        if df.empty or 'user_intent' not in df.columns:
            return None

        intent_counts = df['user_intent'].value_counts().reset_index()
        intent_counts.columns = ['user_intent', 'count']

        fig = px.pie(
            intent_counts,
            values='count',
            names='user_intent',
            title='用戶意圖分佈 (User Intent Distribution)',
            hole=0.3
        )

        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>數量: %{value}<br>佔比: %{percent}<extra></extra>'
        )

        fig.update_layout(
            height=500,
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.05
            )
        )

        return fig

    @staticmethod
    def create_response_time_risk_analysis(df: pd.DataFrame) -> Optional[go.Figure]:
        """
        Create response time risk analysis stacked bar chart by date

        Args:
            df: Filtered DataFrame

        Returns:
            Plotly figure or None if no data
        """
        if df.empty or 'request_timestamp' not in df.columns or 'risk_level' not in df.columns:
            return None

        # Extract date from timestamp
        df_copy = df.copy()
        df_copy['date'] = df_copy['request_timestamp'].dt.date

        # Count by date and risk level
        risk_by_date = df_copy.groupby(['date', 'risk_level']).size().reset_index(name='count')

        # Define risk level order
        risk_order = ['安全 (<3s)', '低風險 (3-5s)', '中風險 (5-8s)', '高風險 (>8s)']
        risk_colors = {
            '安全 (<3s)': '#22c55e',
            '低風險 (3-5s)': '#eab308',
            '中風險 (5-8s)': '#f97316',
            '高風險 (>8s)': '#ef4444'
        }

        # Create stacked bar chart
        fig = go.Figure()

        for risk_level in risk_order:
            risk_data = risk_by_date[risk_by_date['risk_level'] == risk_level]
            fig.add_trace(go.Bar(
                x=risk_data['date'],
                y=risk_data['count'],
                name=risk_level,
                marker_color=risk_colors.get(risk_level, '#gray'),
                hovertemplate='<b>%{x}</b><br>%{fullData.name}<br>數量: %{y}<extra></extra>'
            ))

        fig.update_layout(
            title='回應時間風險分析 (Response Time Risk Analysis)',
            xaxis_title='日期 (Date)',
            yaxis_title='數量 (Count)',
            barmode='stack',
            height=500,
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        return fig

    @staticmethod
    def create_risk_intent_drilldown(df: pd.DataFrame, risk_level: str) -> Optional[go.Figure]:
        """
        Create drill-down chart showing intent distribution for a specific risk level

        Args:
            df: Filtered DataFrame
            risk_level: Selected risk level

        Returns:
            Plotly figure or None if no data
        """
        if df.empty or 'user_intent' not in df.columns or 'risk_level' not in df.columns:
            return None

        # Filter by risk level
        risk_df = df[df['risk_level'] == risk_level]

        if risk_df.empty:
            return None

        intent_counts = risk_df['user_intent'].value_counts().reset_index()
        intent_counts.columns = ['user_intent', 'count']

        fig = px.bar(
            intent_counts,
            x='user_intent',
            y='count',
            title=f'意圖分佈 - {risk_level}',
            labels={'user_intent': '用戶意圖', 'count': '數量'},
            color='count',
            color_continuous_scale='Blues'
        )

        fig.update_layout(
            height=400,
            xaxis_tickangle=-45,
            showlegend=False
        )

        fig.update_traces(
            hovertemplate='<b>%{x}</b><br>數量: %{y}<extra></extra>'
        )

        return fig

    @staticmethod
    def create_key_entity_distribution(df: pd.DataFrame) -> Optional[go.Figure]:
        """
        Create key entity distribution horizontal bar chart

        Args:
            df: Filtered DataFrame

        Returns:
            Plotly figure or None if no data
        """
        if df.empty or 'key_entity' not in df.columns:
            return None

        # Only include "Frequently asked question" intent
        if 'user_intent' in df.columns:
            faq_df = df[df['user_intent'] == 'Frequently asked question']
        else:
            faq_df = df

        # Filter out Unknown, empty values, and "不存在實體"
        entity_df = faq_df[
            faq_df['key_entity'].notna() &
            (faq_df['key_entity'] != 'Unknown') &
            (faq_df['key_entity'] != '') &
            (faq_df['key_entity'] != '不存在實體')
        ]

        if entity_df.empty:
            return None

        entity_counts = entity_df['key_entity'].value_counts().head(20).reset_index()
        entity_counts.columns = ['key_entity', 'count']

        # Sort by count for better visualization
        entity_counts = entity_counts.sort_values('count', ascending=True)

        fig = px.bar(
            entity_counts,
            x='count',
            y='key_entity',
            orientation='h',
            title='關鍵實體分佈 (Key Entity Distribution) - Top 20',
            labels={'key_entity': '關鍵實體', 'count': '出現次數'},
            color='count',
            color_continuous_scale='Viridis'
        )

        fig.update_layout(
            height=600,
            showlegend=False,
            yaxis={'categoryorder': 'total ascending'}
        )

        fig.update_traces(
            hovertemplate='<b>%{y}</b><br>出現次數: %{x}<extra></extra>'
        )

        return fig

    @staticmethod
    def create_wordcloud(df: pd.DataFrame) -> Optional[str]:
        """
        Create word cloud from key entities

        Args:
            df: Filtered DataFrame

        Returns:
            Base64 encoded image string or None if no data
        """
        if df.empty or 'key_entity' not in df.columns:
            return None

        # Only include "Frequently asked question" intent
        if 'user_intent' in df.columns:
            faq_df = df[df['user_intent'] == 'Frequently asked question']
        else:
            faq_df = df

        # Filter out Unknown, empty values, and "不存在實體"
        entity_df = faq_df[
            faq_df['key_entity'].notna() &
            (faq_df['key_entity'] != 'Unknown') &
            (faq_df['key_entity'] != '') &
            (faq_df['key_entity'] != '不存在實體')
        ]

        if entity_df.empty:
            return None

        # Create word frequency dictionary
        entity_freq = entity_df['key_entity'].value_counts().to_dict()

        # Generate word cloud
        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color='white',
            colormap='viridis',
            relative_scaling=0.5,
            min_font_size=10
        ).generate_from_frequencies(entity_freq)

        # Convert to base64 image
        img_buffer = io.BytesIO()
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.tight_layout(pad=0)
        plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
        plt.close()

        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.read()).decode()

        return img_base64

    @staticmethod
    def create_summary_metrics(df: pd.DataFrame) -> dict:
        """
        Calculate summary metrics

        Args:
            df: Filtered DataFrame

        Returns:
            Dictionary of metrics
        """
        if df.empty:
            return {
                'total_conversations': 0,
                'avg_response_time': 0,
                'total_hotels': 0,
                'total_rooms': 0,
                'high_risk_count': 0,
                'high_risk_percentage': 0
            }

        metrics = {
            'total_conversations': len(df),
            'avg_response_time': df['response_timecost'].mean() if 'response_timecost' in df.columns else 0,
            'total_hotels': df['hotel_name'].nunique() if 'hotel_name' in df.columns else 0,
            'total_rooms': df['room_name'].nunique() if 'room_name' in df.columns else 0,
            'high_risk_count': len(df[df['risk_level'] == '高風險 (>8s)']) if 'risk_level' in df.columns else 0,
        }

        metrics['high_risk_percentage'] = (metrics['high_risk_count'] / metrics['total_conversations'] * 100) if metrics['total_conversations'] > 0 else 0

        return metrics
