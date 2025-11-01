"""
SPOT Data Processor for Smart Speaker UI Behavior Analysis
智慧音箱UI介面行為數據處理器
"""

import pandas as pd
from datetime import datetime
from typing import Optional, List, Tuple, Dict
import streamlit as st


class SpotDataProcessor:
    """處理智慧音箱UI行為數據的類別"""

    def __init__(self):
        """初始化數據處理器"""
        self.df: Optional[pd.DataFrame] = None
        self.original_df: Optional[pd.DataFrame] = None

    def load_data(self, uploaded_file) -> bool:
        """
        載入並處理上傳的CSV檔案

        Args:
            uploaded_file: Streamlit上傳的檔案物件

        Returns:
            bool: 載入成功返回True，失敗返回False
        """
        try:
            # 讀取CSV檔案
            df = pd.read_csv(uploaded_file)

            # 檢查數據大小限制
            if len(df) > 100000:
                st.error("❌ 檔案過大，請分批上傳（限制：100,000筆以內）")
                return False

            # 執行欄位映射
            self.original_df = df.copy()
            self.df = self._map_columns(df)

            if self.df is None:
                return False

            # 數據清理和預處理
            self._preprocess_data()

            st.success(f"✅ 成功載入 {len(self.df):,} 筆UI行為數據")
            return True

        except Exception as e:
            st.error(f"❌ 檔案讀取失敗：{str(e)}")
            return False

    def _map_columns(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        映射原始欄位名稱到標準化名稱

        Args:
            df: 原始數據框

        Returns:
            Optional[pd.DataFrame]: 映射後的數據框，失敗返回None
        """
        # 定義欄位映射關係
        column_mapping = {
            "device_info.room.hotel_name": "hotel_name",
            "device_info.MAC": "device_id",
            "device_info.room.room_no": "room_name",
            "event_trigger.type": "interaction",
            "event_trigger.intent.subject": "query_intent",
            "event_trigger.intent.action": "intent_action",
            "event_trigger.data": "data",
            "event_trigger.request": "voice_request",
            "event_trigger.response": "voice_response",
        }

        try:
            # 檢查必要欄位是否存在
            missing_columns = []
            for original_col in column_mapping.keys():
                if original_col not in df.columns:
                    missing_columns.append(original_col)

            if missing_columns:
                st.error(f"❌ 缺少必要欄位：{', '.join(missing_columns)}")
                return None

            # 執行欄位映射
            mapped_df = df.rename(columns=column_mapping)

            # 保留映射後的欄位
            required_columns = list(column_mapping.values())
            available_columns = [
                col for col in required_columns if col in mapped_df.columns
            ]
            mapped_df = mapped_df[available_columns]

            return mapped_df

        except Exception as e:
            st.error(f"❌ 欄位映射失敗：{str(e)}")
            return None

    def _preprocess_data(self):
        """數據預處理"""
        if self.df is None:
            return

        # 處理空值
        self.df = self.df.fillna("")

        # 標準化互動方式類別
        interaction_mapping = {
            "UI": "UI",
            "HARDWARE": "HARDWARE",
            "SYSTEM": "SYSTEM",
            "VOICE": "VOICE",
        }

        # 確保互動方式在預期範圍內
        if "interaction" in self.df.columns:
            self.df["interaction"] = (
                self.df["interaction"].map(interaction_mapping).fillna("UNKNOWN")
            )

        # 添加時間戳（如果沒有的話，使用當前時間）
        if "timestamp" not in self.df.columns:
            self.df["timestamp"] = datetime.now()

    def get_filtered_data(
        self,
        hotel_filter: List[str] = None,
        room_filter: List[str] = None,
        device_filter: List[str] = None,
        interaction_filter: List[str] = None,
        intent_filter: List[str] = None,
    ) -> pd.DataFrame:
        """
        根據篩選條件返回過濾後的數據

        Args:
            hotel_filter: 飯店名稱篩選
            room_filter: 房間號碼篩選
            device_filter: 設備ID篩選
            interaction_filter: 互動方式篩選
            intent_filter: 意圖篩選

        Returns:
            pd.DataFrame: 過濾後的數據框
        """
        if self.df is None:
            return pd.DataFrame()

        filtered_df = self.df.copy()

        # 應用各種篩選條件
        if hotel_filter and len(hotel_filter) > 0:
            filtered_df = filtered_df[filtered_df["hotel_name"].isin(hotel_filter)]

        if room_filter and len(room_filter) > 0:
            filtered_df = filtered_df[filtered_df["room_name"].isin(room_filter)]

        if device_filter and len(device_filter) > 0:
            filtered_df = filtered_df[filtered_df["device_id"].isin(device_filter)]

        if interaction_filter and len(interaction_filter) > 0:
            filtered_df = filtered_df[
                filtered_df["interaction"].isin(interaction_filter)
            ]

        if intent_filter and len(intent_filter) > 0:
            filtered_df = filtered_df[filtered_df["query_intent"].isin(intent_filter)]

        return filtered_df

    def get_interaction_distribution(self, df: pd.DataFrame = None) -> Dict:
        """
        獲取互動方式分佈統計

        Args:
            df: 可選的數據框，如果不提供則使用全部數據

        Returns:
            Dict: 包含原始和融合分佈的字典
        """
        if df is None:
            df = self.df

        if df is None or df.empty:
            return {"raw": {}, "merged": {}}

        # 原始互動方式分佈
        raw_distribution = df["interaction"].value_counts().to_dict()

        # 融合互動方式分佈（UI + SYSTEM 合併）
        merged_df = df.copy()
        merged_df["interaction_merged"] = merged_df["interaction"].apply(
            lambda x: "UI_SYSTEM" if x in ["UI", "SYSTEM"] else x
        )
        merged_distribution = merged_df["interaction_merged"].value_counts().to_dict()

        # 重命名融合類別
        if "UI_SYSTEM" in merged_distribution:
            merged_distribution["UI + SYSTEM"] = merged_distribution.pop("UI_SYSTEM")

        return {"raw": raw_distribution, "merged": merged_distribution}

    def get_intent_distribution(
        self, df: pd.DataFrame = None, merge_small: bool = False, threshold: float = 1.0
    ) -> Dict:
        """
        獲取用戶意圖分佈統計

        Args:
            df: 可選的數據框，如果不提供則使用全部數據
            merge_small: 是否將小比例意圖合併為"其他"
            threshold: 合併閾值，預設為1.0%

        Returns:
            Dict: 意圖分佈字典，包含 'distribution' 和可能的 'others_breakdown'
        """
        if df is None:
            df = self.df

        if df is None or df.empty:
            return {}

        # 獲取原始分佈
        raw_counts = df["query_intent"].value_counts().to_dict()

        if not merge_small:
            return raw_counts

        # 計算總數
        total_count = sum(raw_counts.values())

        # 分離大於和小於閾值的意圖
        main_intents = {}
        small_intents = {}

        for intent, count in raw_counts.items():
            percentage = (count / total_count) * 100
            if percentage >= threshold:
                main_intents[intent] = count
            else:
                small_intents[intent] = count

        # 如果有小比例意圖，加入"其他"
        result = {
            "distribution": main_intents.copy(),
            "others_breakdown": small_intents if small_intents else {},
        }

        if small_intents:
            others_total = sum(small_intents.values())
            result["distribution"]["其他"] = others_total

        return result

    def get_module_not_support_details(self, df: pd.DataFrame = None) -> pd.DataFrame:
        """
        獲取MODULE_NOT_SUPPORT錯誤詳情

        Args:
            df: 可選的數據框，如果不提供則使用全部數據

        Returns:
            pd.DataFrame: 包含錯誤詳情的數據框
        """
        if df is None:
            df = self.df

        if df is None or df.empty:
            return pd.DataFrame()

        # 篩選MODULE_NOT_SUPPORT記錄
        error_df = df[df["query_intent"] == "MODULE_NOT_SUPPORT"].copy()

        # 選擇相關欄位
        relevant_columns = [
            "hotel_name",
            "room_name",
            "device_id",
            "interaction",
            "intent_action",
            "data",
            "voice_request",
            "voice_response",
        ]

        # 只保留存在的欄位
        available_columns = [col for col in relevant_columns if col in error_df.columns]
        error_df = error_df[available_columns]

        return error_df

    def get_summary_stats(self, df: pd.DataFrame = None) -> Dict:
        """
        獲取統計摘要

        Args:
            df: 可選的數據框，如果不提供則使用全部數據

        Returns:
            Dict: 統計摘要字典
        """
        if df is None:
            df = self.df

        if df is None or df.empty:
            return {
                "total_interactions": 0,
                "active_devices": 0,
                "error_rate": 0,
                "top_rooms": [],
            }

        total_interactions = len(df)
        active_devices = df["device_id"].nunique() if "device_id" in df.columns else 0

        # 計算錯誤率
        error_count = (
            len(df[df["query_intent"] == "MODULE_NOT_SUPPORT"])
            if "query_intent" in df.columns
            else 0
        )
        error_rate = (
            (error_count / total_interactions * 100) if total_interactions > 0 else 0
        )

        # 最活躍房間（前5名）
        top_rooms = []
        if "room_name" in df.columns:
            room_counts = df["room_name"].value_counts().head(5)
            top_rooms = [
                {"room": room, "count": count} for room, count in room_counts.items()
            ]

        return {
            "total_interactions": total_interactions,
            "active_devices": active_devices,
            "error_rate": error_rate,
            "top_rooms": top_rooms,
        }

    def get_filter_options(self) -> Dict:
        """
        獲取篩選器選項

        Returns:
            Dict: 包含各種篩選器選項的字典
        """
        if self.df is None or self.df.empty:
            return {
                "hotels": [],
                "rooms": [],
                "devices": [],
                "interactions": [],
                "intents": [],
            }

        return {
            "hotels": (
                sorted(self.df["hotel_name"].unique().tolist())
                if "hotel_name" in self.df.columns
                else []
            ),
            "rooms": (
                sorted(self.df["room_name"].unique().tolist())
                if "room_name" in self.df.columns
                else []
            ),
            "devices": (
                sorted(self.df["device_id"].unique().tolist())
                if "device_id" in self.df.columns
                else []
            ),
            "interactions": (
                sorted(self.df["interaction"].unique().tolist())
                if "interaction" in self.df.columns
                else []
            ),
            "intents": (
                sorted(self.df["query_intent"].unique().tolist())
                if "query_intent" in self.df.columns
                else []
            ),
        }
