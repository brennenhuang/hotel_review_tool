"""
Data processor module for Smart Speaker Conversation Analysis Platform
Handles data loading, column mapping, and transformations
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import List, Tuple, Optional


class DataProcessor:
    """Process and transform conversation data"""

    # Column mapping from original to standardized names
    COLUMN_MAPPING = {
        "final_output.metadata.queryText": "user_query",
        "final_output.res": "chatbot_response",
        "performance.metadata.language_code": "user_language",
        "final_output.metadata.hotelName": "hotel_name",
        "performance.service_info.total.timecost": "response_timecost",
        "final_output.metadata.roomName": "room_name",
        "time": "request_timestamp",
        "final_output.metadata.conversation_id": "conversation_id",
        "final_output.key_entity": "key_entity",
    }

    # Risk level thresholds (in seconds)
    RISK_LEVELS = {
        "safe": (0, 3),
        "low_risk": (3, 5),
        "medium_risk": (5, 8),
        "high_risk": (8, float("inf")),
    }

    def __init__(self):
        self.df = None
        self.original_df = None

    def load_and_process_csv(self, file) -> Tuple[bool, str]:
        """
        Load CSV file and process it

        Args:
            file: Uploaded file object from Streamlit

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Read CSV
            df = pd.read_csv(file)

            # Check row limit
            if len(df) > 100000:
                return False, "檔案過大，請分批上傳（最多100,000筆）"

            # Store original data
            self.original_df = df.copy()

            # Map columns
            df = self._map_columns(df)

            # Process user_intent (prefer intent_name_en over intent_name)
            if (
                "final_output.intent_name_en" in self.original_df.columns
                and "final_output.intent_name" in self.original_df.columns
            ):
                df["user_intent"] = self.original_df[
                    "final_output.intent_name_en"
                ].fillna(self.original_df["final_output.intent_name"])
            elif "final_output.intent_name_en" in self.original_df.columns:
                df["user_intent"] = self.original_df["final_output.intent_name_en"]
            elif "final_output.intent_name" in self.original_df.columns:
                df["user_intent"] = self.original_df["final_output.intent_name"]

            # Convert timestamp to datetime
            # Handle special format like "Oct 15, 2025 @ 11:54:40.903"
            df["request_timestamp"] = df["request_timestamp"].apply(
                self._parse_timestamp
            )

            # Convert response_timecost to numeric
            df["response_timecost"] = pd.to_numeric(
                df["response_timecost"], errors="coerce"
            )

            # Add risk level column
            df["risk_level"] = df["response_timecost"].apply(self._calculate_risk_level)

            # Fill NaN values for categorical columns
            categorical_cols = [
                "hotel_name",
                "room_name",
                "user_intent",
                "user_language",
                "key_entity",
            ]
            for col in categorical_cols:
                if col in df.columns:
                    df[col] = df[col].fillna("Unknown")

            self.df = df
            return True, f"成功載入 {len(df)} 筆數據"

        except Exception as e:
            return False, f"載入失敗：{str(e)}"

    def _map_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Map original column names to standardized names"""
        mapped_df = pd.DataFrame()

        for original_col, standard_col in self.COLUMN_MAPPING.items():
            if original_col in df.columns:
                mapped_df[standard_col] = df[original_col]

        return mapped_df

    def _parse_timestamp(self, timestamp_str):
        """
        Parse timestamp string in various formats
        Handles formats like:
        - "Oct 15, 2025 @ 11:54:40.903"
        - Standard ISO formats
        - Unix timestamps
        """
        if pd.isna(timestamp_str):
            return pd.NaT

        timestamp_str = str(timestamp_str).strip()

        # Handle format like "Oct 15, 2025 @ 11:54:40.903"
        if "@" in timestamp_str:
            try:
                # Remove @ and extra spaces, then parse with specific format
                cleaned = timestamp_str.replace(" @", "").strip()
                # Try common format: "Oct 15, 2025 11:54:40.903"
                return pd.to_datetime(
                    cleaned, format="%b %d, %Y %H:%M:%S.%f", errors="raise"
                )
            except (ValueError, TypeError):
                try:
                    # Try without microseconds: "Oct 15, 2025 11:54:40"
                    cleaned = timestamp_str.replace(" @", "").strip()
                    return pd.to_datetime(
                        cleaned, format="%b %d, %Y %H:%M:%S", errors="raise"
                    )
                except (ValueError, TypeError):
                    # Fallback to general parsing for @ format
                    cleaned = timestamp_str.replace(" @", "").strip()
                    return pd.to_datetime(cleaned, infer_datetime_format=True)

        # Try common ISO formats first
        try:
            # ISO format with microseconds
            return pd.to_datetime(
                timestamp_str, format="%Y-%m-%d %H:%M:%S.%f", errors="raise"
            )
        except (ValueError, TypeError):
            pass

        try:
            # ISO format without microseconds
            return pd.to_datetime(
                timestamp_str, format="%Y-%m-%d %H:%M:%S", errors="raise"
            )
        except (ValueError, TypeError):
            pass

        try:
            # ISO date only
            return pd.to_datetime(timestamp_str, format="%Y-%m-%d", errors="raise")
        except (ValueError, TypeError):
            pass

        try:
            # Try with infer_datetime_format as last resort before fallback
            return pd.to_datetime(timestamp_str, infer_datetime_format=True)
        except (ValueError, TypeError):
            pass

        # If all else fails, return NaT
        return pd.NaT

    def _calculate_risk_level(self, timecost: float) -> str:
        """Calculate risk level based on response time"""
        if pd.isna(timecost):
            return "Unknown"

        if timecost < 3:
            return "安全 (<3s)"
        elif timecost < 5:
            return "低風險 (3-5s)"
        elif timecost < 8:
            return "中風險 (5-8s)"
        else:
            return "高風險 (>8s)"

    def get_data(self) -> Optional[pd.DataFrame]:
        """Get processed data"""
        return self.df

    def filter_data(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_timecost: Optional[float] = None,
        max_timecost: Optional[float] = None,
        hotel_names: Optional[List[str]] = None,
        room_names: Optional[List[str]] = None,
        user_intents: Optional[List[str]] = None,
        user_languages: Optional[List[str]] = None,
        risk_levels: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Filter data based on given criteria

        Returns:
            Filtered DataFrame
        """
        if self.df is None:
            return pd.DataFrame()

        filtered_df = self.df.copy()

        # Time range filter
        if start_date is not None:
            filtered_df = filtered_df[filtered_df["request_timestamp"] >= start_date]
        if end_date is not None:
            # Add one day to include the end_date fully
            end_date_inclusive = end_date + timedelta(days=1)
            filtered_df = filtered_df[
                filtered_df["request_timestamp"] < end_date_inclusive
            ]

        # Response timecost filter
        if min_timecost is not None:
            filtered_df = filtered_df[filtered_df["response_timecost"] >= min_timecost]
        if max_timecost is not None:
            filtered_df = filtered_df[filtered_df["response_timecost"] <= max_timecost]

        # Categorical filters
        if hotel_names and len(hotel_names) > 0:
            filtered_df = filtered_df[filtered_df["hotel_name"].isin(hotel_names)]
        if room_names and len(room_names) > 0:
            filtered_df = filtered_df[filtered_df["room_name"].isin(room_names)]
        if user_intents and len(user_intents) > 0:
            filtered_df = filtered_df[filtered_df["user_intent"].isin(user_intents)]
        if user_languages and len(user_languages) > 0:
            filtered_df = filtered_df[filtered_df["user_language"].isin(user_languages)]
        if risk_levels and len(risk_levels) > 0:
            filtered_df = filtered_df[filtered_df["risk_level"].isin(risk_levels)]

        return filtered_df

    def get_unique_values(self, column: str) -> List[str]:
        """Get unique values for a column"""
        if self.df is None or column not in self.df.columns:
            return []
        return sorted(self.df[column].unique().tolist())

    def get_date_range(self) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Get min and max dates from the dataset"""
        if self.df is None or "request_timestamp" not in self.df.columns:
            return None, None
        return self.df["request_timestamp"].min(), self.df["request_timestamp"].max()

    def get_timecost_range(self) -> Tuple[float, float]:
        """Get min and max response timecost"""
        if self.df is None or "response_timecost" not in self.df.columns:
            return 0.0, 10.0
        return float(self.df["response_timecost"].min()), float(
            self.df["response_timecost"].max()
        )
