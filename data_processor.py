"""
Data processor module for Smart Speaker Conversation Analysis Platform
Handles data loading, column mapping, and transformations
"""

from datetime import datetime, time, timedelta
from typing import List, Optional, Tuple

import pandas as pd
import pytz


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
        min_date = self.df["request_timestamp"].min()
        max_date = self.df["request_timestamp"].max()
        return min_date, max_date

    def get_timecost_range(self) -> Tuple[float, float]:
        """Get min and max response timecost"""
        if self.df is None or "response_timecost" not in self.df.columns:
            return 0.0, 10.0
        return float(self.df["response_timecost"].min()), float(
            self.df["response_timecost"].max()
        )

    def get_available_timezones(self) -> List[Tuple[str, str]]:
        """
        Get list of commonly used timezones for selection

        Returns:
            List of tuples (timezone_id, display_name)
        """
        common_timezones = [
            ("UTC", "UTC (協調世界時)"),
            ("Asia/Taipei", "UTC+8 (台北時間)"),
            ("Asia/Shanghai", "UTC+8 (上海時間)"),
            ("Asia/Hong_Kong", "UTC+8 (香港時間)"),
            ("Asia/Singapore", "UTC+8 (新加坡時間)"),
            ("Asia/Tokyo", "UTC+9 (東京時間)"),
            ("Europe/London", "UTC+0/+1 (倫敦時間)"),
            ("America/New_York", "UTC-5/-4 (紐約時間)"),
            ("America/Los_Angeles", "UTC-8/-7 (洛杉磯時間)"),
        ]
        return common_timezones

    def get_timezone_info(self, timezone_id: str, dst_override: str = None) -> str:
        """
        獲取時區的夏令時狀態信息

        Args:
            timezone_id: 時區ID (如 'America/New_York')
            dst_override: 強制選擇模式 ("自動", "強制夏令時", "強制標準時間")

        Returns:
            時區狀態字符串
        """
        try:
            import pytz
            from datetime import datetime

            if timezone_id in [
                "UTC",
                "Asia/Taipei",
                "Asia/Shanghai",
                "Asia/Hong_Kong",
                "Asia/Singapore",
            ]:
                return ""  # 這些時區不使用夏令時，不需要額外信息

            tz = pytz.timezone(timezone_id)
            now = datetime.now(tz)

            # 確定是否使用夏令時
            if dst_override == "強制夏令時":
                is_dst = True
                mode_indicator = "(強制)"
            elif dst_override == "強制標準時間":
                is_dst = False
                mode_indicator = "(強制)"
            else:  # 自動模式
                is_dst = bool(now.dst())
                mode_indicator = "(自動)"

            # 計算對應的UTC偏移量
            if dst_override in ["強制夏令時", "強制標準時間"]:
                # 強制模式：計算對應的偏移量
                utc_offset_formatted = self._calculate_forced_offset(
                    timezone_id, is_dst
                )
            else:
                # 自動模式：使用當前偏移量
                utc_offset = now.strftime("%z")
                utc_offset_formatted = f"{utc_offset[:3]}:{utc_offset[3:]}"

            dst_emoji = "🌞" if is_dst else "❄️"
            dst_status = "夏令時" if is_dst else "標準時間"

            return f"\n{dst_status}: UTC{utc_offset_formatted} {mode_indicator}"

        except Exception:
            return ""

    def _calculate_forced_offset(self, timezone_id: str, force_dst: bool) -> str:
        """
        計算強制模式下的UTC偏移量

        Args:
            timezone_id: 時區ID
            force_dst: 是否強制夏令時

        Returns:
            格式化的UTC偏移量字符串
        """
        # 常見時區的標準時間和夏令時偏移量
        timezone_offsets = {
            "America/New_York": {False: "-05:00", True: "-04:00"},  # EST/EDT
            "America/Los_Angeles": {False: "-08:00", True: "-07:00"},  # PST/PDT
            "Europe/London": {False: "+00:00", True: "+01:00"},  # GMT/BST
        }

        if timezone_id in timezone_offsets:
            return timezone_offsets[timezone_id][force_dst]
        else:
            # 對於其他時區，嘗試動態計算
            try:
                import pytz
                from datetime import datetime

                tz = pytz.timezone(timezone_id)

                # 使用一個已知的夏令時日期和標準時間日期來計算偏移量
                summer_date = datetime(2024, 7, 15, 12, 0, 0)  # 夏季日期
                winter_date = datetime(2024, 1, 15, 12, 0, 0)  # 冬季日期

                if force_dst:
                    test_dt = tz.localize(summer_date)
                else:
                    test_dt = tz.localize(winter_date)

                offset = test_dt.strftime("%z")
                return f"{offset[:3]}:{offset[3:]}"
            except Exception:
                return "+00:00"  # 默認值

    def convert_timezone(
        self,
        source_timezone: str = "Asia/Taipei",
        target_timezone: str = "UTC",
        dst_override: str = None,
    ) -> Optional[pd.DataFrame]:
        """
        Convert timestamps from source timezone to target timezone

        Args:
            source_timezone: Source timezone (default: Asia/Taipei for UTC+8)
            target_timezone: Target timezone for conversion
            dst_override: 強制選擇模式 ("自動", "強制夏令時", "強制標準時間")

        Returns:
            DataFrame with converted timestamps, or None if no data
        """
        if self.df is None:
            return None

        df_converted = self.df.copy()

        try:
            # Define timezones
            source_tz = pytz.timezone(source_timezone)
            target_tz = pytz.timezone(target_timezone)

            # Convert timestamps with DST override consideration
            df_converted["request_timestamp"] = df_converted["request_timestamp"].apply(
                lambda x: self._convert_single_timestamp_with_override(
                    x, source_tz, target_tz, dst_override
                )
            )

            return df_converted

        except Exception as e:
            print(f"Timezone conversion error: {e}")
            return self.df.copy()

    def _convert_single_timestamp(self, timestamp, source_tz, target_tz) -> datetime:
        """
        Convert a single timestamp between timezones

        Args:
            timestamp: Input timestamp
            source_tz: Source timezone object
            target_tz: Target timezone object

        Returns:
            Converted timestamp
        """
        if pd.isna(timestamp):
            return timestamp

        try:
            # If timestamp is naive (no timezone info), localize it to source timezone
            if timestamp.tzinfo is None:
                localized_ts = source_tz.localize(timestamp)
            else:
                # If already has timezone info, convert to source timezone
                localized_ts = timestamp.astimezone(source_tz)

            # Convert to target timezone
            converted_ts = localized_ts.astimezone(target_tz)

            # Return as naive timestamp in target timezone
            return converted_ts.replace(tzinfo=None)

        except Exception as e:
            print(f"Single timestamp conversion error: {e}")
            return timestamp

    def _convert_single_timestamp_with_override(
        self, timestamp, source_tz, target_tz, dst_override
    ) -> datetime:
        """
        Convert a single timestamp between timezones with DST override support

        Args:
            timestamp: Input timestamp
            source_tz: Source timezone object
            target_tz: Target timezone object
            dst_override: 強制選擇模式 ("自動", "強制夏令時", "強制標準時間")

        Returns:
            Converted timestamp
        """
        if pd.isna(timestamp):
            return timestamp

        try:
            # First do normal conversion
            normal_converted = self._convert_single_timestamp(
                timestamp, source_tz, target_tz
            )

            # If no override or auto mode, return normal conversion
            if not dst_override or dst_override == "自動":
                return normal_converted

            # For forced modes, calculate the adjustment
            target_tz_name = str(target_tz)

            # Only apply adjustment for DST-capable timezones
            if target_tz_name in [
                "America/New_York",
                "America/Los_Angeles",
                "Europe/London",
            ]:
                # Get what the timezone would be in both DST and standard time
                summer_test = datetime(
                    timestamp.year,
                    7,
                    15,
                    timestamp.hour,
                    timestamp.minute,
                    timestamp.second,
                )
                winter_test = datetime(
                    timestamp.year,
                    1,
                    15,
                    timestamp.hour,
                    timestamp.minute,
                    timestamp.second,
                )

                try:
                    # Localize test times to source timezone
                    summer_source = source_tz.localize(summer_test)
                    winter_source = source_tz.localize(winter_test)

                    # Convert to target timezone
                    summer_target = summer_source.astimezone(target_tz).replace(
                        tzinfo=None
                    )
                    winter_target = winter_source.astimezone(target_tz).replace(
                        tzinfo=None
                    )

                    # Calculate DST offset (difference between summer and winter)
                    dst_offset = (summer_target.hour - winter_target.hour) % 24

                    if dst_override == "強制夏令時":
                        # If we want DST but currently have standard time
                        test_localized = source_tz.localize(
                            timestamp.replace(tzinfo=None)
                        )
                        test_converted = test_localized.astimezone(target_tz)
                        is_currently_dst = bool(test_converted.dst())

                        if not is_currently_dst and dst_offset > 0:
                            return normal_converted + timedelta(hours=dst_offset)

                    elif dst_override == "強制標準時間":
                        # If we want standard time but currently have DST
                        test_localized = source_tz.localize(
                            timestamp.replace(tzinfo=None)
                        )
                        test_converted = test_localized.astimezone(target_tz)
                        is_currently_dst = bool(test_converted.dst())

                        if is_currently_dst and dst_offset > 0:
                            return normal_converted - timedelta(hours=dst_offset)

                except Exception:
                    pass

            return normal_converted

        except Exception as e:
            print(f"Single timestamp conversion with override error: {e}")
            return timestamp

    def convert_time_to_timezone(
        self,
        time_obj: time,
        date_reference: datetime,
        source_timezone: str = "Asia/Taipei",
        target_timezone: str = "UTC",
    ) -> time:
        """
        Convert a time object from source timezone to target timezone

        Args:
            time_obj: Time object to convert (e.g., 14:00 for check-in)
            date_reference: Reference date for the conversion
            source_timezone: Source timezone (default: Asia/Taipei)
            target_timezone: Target timezone for conversion

        Returns:
            Converted time object in target timezone
        """
        try:
            # Create a datetime with the reference date and time
            dt_with_time = datetime.combine(date_reference.date(), time_obj)

            # Convert using existing method
            source_tz = pytz.timezone(source_timezone)
            target_tz = pytz.timezone(target_timezone)

            converted_dt = self._convert_single_timestamp(
                dt_with_time, source_tz, target_tz
            )

            # Return only the time part
            return converted_dt.time()

        except Exception as e:
            print(f"Time conversion error: {e}")
            return time_obj
