"""
Export manager module for Smart Speaker Conversation Analysis Platform
Handles conversation export with stay session segmentation
"""

from datetime import datetime, time, timedelta
from typing import Dict, List, Tuple

import pandas as pd
import pytz


class ExportManager:
    """Manage data export with intelligent stay session segmentation"""

    def __init__(self):
        pass

    def segment_by_stay_sessions(
        self, df: pd.DataFrame, checkin_time_str: str, checkout_time_str: str
    ) -> List[Dict]:
        """
        Segment conversations by stay sessions

        Args:
            df: Filtered DataFrame with conversation data
            checkin_time_str: Standard check-in time (e.g., "14:00")
            checkout_time_str: Standard check-out time (e.g., "11:00")

        Returns:
            List of stay session dictionaries
        """
        if df.empty:
            return []

        # Parse check-in and check-out times
        checkin_time = datetime.strptime(checkin_time_str, "%H:%M").time()
        checkout_time = datetime.strptime(checkout_time_str, "%H:%M").time()

        # Sort by hotel, room, and timestamp
        df_sorted = df.sort_values(
            ["hotel_name", "room_name", "request_timestamp"]
        ).copy()

        sessions = []

        # Group by hotel and room
        for (hotel, room), group_df in df_sorted.groupby(["hotel_name", "room_name"]):
            # Process each room's conversations
            room_sessions = self._segment_room_conversations(
                group_df, hotel, room, checkin_time, checkout_time
            )
            sessions.extend(room_sessions)

        return sessions

    def _segment_room_conversations(
        self,
        room_df: pd.DataFrame,
        hotel: str,
        room: str,
        checkin_time: time,
        checkout_time: time,
    ) -> List[Dict]:
        """
        Segment conversations for a single room into stay sessions

        Args:
            room_df: DataFrame of conversations for one room
            hotel: Hotel name
            room: Room name
            checkin_time: Standard check-in time
            checkout_time: Standard check-out time

        Returns:
            List of stay session dictionaries
        """
        sessions = []
        current_session = None
        current_conversations = []

        for _, row in room_df.iterrows():
            timestamp = row["request_timestamp"]

            # Determine if this conversation belongs to current session or starts a new one
            if current_session is None:
                # Start first session
                current_session = self._create_session_boundaries(
                    timestamp, checkin_time, checkout_time
                )
                current_conversations = [row]
            elif self._is_in_session(timestamp, current_session):
                # Add to current session
                current_conversations.append(row)
            else:
                # Save current session and start new one
                if current_conversations:
                    sessions.append(
                        {
                            "hotel": hotel,
                            "room": room,
                            "start_time": current_session["start"],
                            "end_time": current_session["end"],
                            "conversations": current_conversations,
                        }
                    )

                # Start new session
                current_session = self._create_session_boundaries(
                    timestamp, checkin_time, checkout_time
                )
                current_conversations = [row]

        # Don't forget the last session
        if current_conversations:
            sessions.append(
                {
                    "hotel": hotel,
                    "room": room,
                    "start_time": current_session["start"],
                    "end_time": current_session["end"],
                    "conversations": current_conversations,
                }
            )

        return sessions

    def _create_session_boundaries(
        self, timestamp: datetime, checkin_time: time, checkout_time: time
    ) -> Dict:
        """
        Create session boundaries based on a timestamp

        Args:
            timestamp: A conversation timestamp
            checkin_time: Standard check-in time
            checkout_time: Standard check-out time

        Returns:
            Dictionary with 'start' and 'end' datetime
        """
        # Find the check-in date for this conversation
        conversation_time = timestamp.time()

        if conversation_time >= checkin_time:
            # Conversation after check-in time - belongs to session starting today
            checkin_datetime = datetime.combine(timestamp.date(), checkin_time)
        else:
            # Conversation before check-in time - belongs to session starting yesterday
            checkin_datetime = datetime.combine(
                timestamp.date() - timedelta(days=1), checkin_time
            )

        # Calculate check-out datetime
        if checkout_time <= checkin_time:
            # Check-out is next day (e.g., check-in 14:00, check-out 11:00)
            checkout_datetime = datetime.combine(
                checkin_datetime.date() + timedelta(days=1), checkout_time
            )
        else:
            # Check-out is same day (unusual but possible)
            checkout_datetime = datetime.combine(checkin_datetime.date(), checkout_time)

        return {"start": checkin_datetime, "end": checkout_datetime}

    def _is_in_session(self, timestamp: datetime, session: Dict) -> bool:
        """
        Check if a timestamp falls within a session

        Args:
            timestamp: Conversation timestamp
            session: Session dictionary with 'start' and 'end'

        Returns:
            True if timestamp is in session, False otherwise
        """
        return session["start"] <= timestamp < session["end"]

    def _convert_session_time_to_local(self, session_time, from_timezone, to_timezone):
        """
        Convert session boundary time back to local timezone for display

        Args:
            session_time: Session boundary datetime
            from_timezone: Current timezone of the session time
            to_timezone: Target timezone (local hotel time)

        Returns:
            Converted datetime in local timezone
        """
        try:
            from_tz = pytz.timezone(from_timezone)
            to_tz = pytz.timezone(to_timezone)

            # Localize the session time to from_timezone
            localized_time = from_tz.localize(session_time.replace(tzinfo=None))

            # Convert to target timezone
            converted_time = localized_time.astimezone(to_tz)

            # Return as naive datetime
            return converted_time.replace(tzinfo=None)

        except Exception as e:
            print(f"Session time conversion error: {e}")
            return session_time

    def generate_export_text(
        self, sessions: List[Dict], export_date: str = None, target_timezone: str = None
    ) -> str:
        """
        Generate formatted text report from stay sessions

        Args:
            sessions: List of stay session dictionaries
            export_date: Export date string (defaults to today)
            target_timezone: Target timezone for display (e.g., 'UTC', 'Asia/Taipei')

        Returns:
            Formatted text report
        """
        if not export_date:
            export_date = datetime.now().strftime("%Y-%m-%d")

        # Determine timezone display name
        timezone_display = ""
        if target_timezone:
            try:
                if target_timezone == "UTC":
                    timezone_display = " (UTC時間)"
                elif "Asia/Taipei" in target_timezone:
                    timezone_display = " (台北時間 UTC+8)"
                else:
                    timezone_display = f" ({target_timezone})"
            except (KeyError, ValueError):
                timezone_display = ""

        # Header
        lines = [
            "智能音箱對話分析報告",
            f"導出日期：{export_date}{timezone_display}",
            f"總共 {len(sessions)} 個住宿時段",
            "=" * 80,
            "",
        ]

        # Add each session
        for i, session in enumerate(sessions, 1):
            hotel = session["hotel"]
            room = session["room"]

            # Use display times if available (for timezone-corrected display)
            if "display_start_time" in session and "display_end_time" in session:
                start_time = session["display_start_time"].strftime("%Y-%m-%d %H:%M")
                end_time = session["display_end_time"].strftime("%Y-%m-%d %H:%M")
            else:
                start_time = session["start_time"].strftime("%Y-%m-%d %H:%M")
                end_time = session["end_time"].strftime("%Y-%m-%d %H:%M")

            lines.append(f"## 用戶體驗報告 ({hotel} - {room})")
            lines.append(f"### 住宿期間：{start_time} ~ {end_time}")
            lines.append("")

            # Add conversations
            for conv in session["conversations"]:
                timestamp = conv["request_timestamp"].strftime("%Y-%m-%d %H:%M:%S")
                conv_id = conv.get("conversation_id", "N/A")
                user_query = conv.get("user_query", "")
                chatbot_response = conv.get("chatbot_response", "")
                timecost = conv.get("response_timecost", 0)

                lines.append(f"[{timestamp}], (ID: {conv_id})")
                lines.append(f"user：{user_query}")
                lines.append(f"chatbot: {chatbot_response} (思考時間:{timecost:.2f}s)")
                lines.append("")

            lines.append("---")
            lines.append("")

        return "\n".join(lines)

    def export_to_file(
        self,
        df: pd.DataFrame,
        checkin_time: str,
        checkout_time: str,
        filename: str = None,
        target_timezone: str = None,
        source_timezone: str = None,
    ) -> Tuple[str, str]:
        """
        Complete export workflow

        Args:
            df: Filtered DataFrame (may be timezone-converted)
            checkin_time: Check-in time string in local hotel time (e.g., "14:00")
            checkout_time: Check-out time string in local hotel time (e.g., "11:00")
            filename: Optional filename
            target_timezone: Target timezone for display (e.g., 'UTC', 'Asia/Taipei')
            source_timezone: Source timezone if data was converted (e.g., 'Asia/Taipei')

        Returns:
            Tuple of (content: str, filename: str)
        """
        # Handle timezone conversion for session segmentation
        if source_timezone and target_timezone and source_timezone != target_timezone:
            # Data has been timezone converted, need to convert checkin/checkout times for comparison
            # Use first timestamp as reference for date
            if not df.empty:
                sample_date = df["request_timestamp"].iloc[0]

                # Convert local hotel times to data timezone for session segmentation
                from datetime import time as time_cls

                checkin_parts = checkin_time.split(":")
                checkout_parts = checkout_time.split(":")
                checkin_time_obj = time_cls(
                    int(checkin_parts[0]), int(checkin_parts[1])
                )
                checkout_time_obj = time_cls(
                    int(checkout_parts[0]), int(checkout_parts[1])
                )

                # Create a datetime with sample date and local times
                sample_checkin_dt = datetime.combine(
                    sample_date.date(), checkin_time_obj
                )
                sample_checkout_dt = datetime.combine(
                    sample_date.date(), checkout_time_obj
                )

                # Convert to source timezone then to target timezone for comparison
                source_tz = pytz.timezone(source_timezone)
                target_tz = pytz.timezone(target_timezone)

                # Localize to source timezone
                localized_checkin = source_tz.localize(
                    sample_checkin_dt.replace(tzinfo=None)
                )
                localized_checkout = source_tz.localize(
                    sample_checkout_dt.replace(tzinfo=None)
                )

                # Convert to target timezone
                converted_checkin = localized_checkin.astimezone(target_tz)
                converted_checkout = localized_checkout.astimezone(target_tz)

                # Use converted times for session segmentation
                segmentation_checkin = converted_checkin.strftime("%H:%M")
                segmentation_checkout = converted_checkout.strftime("%H:%M")
            else:
                segmentation_checkin = checkin_time
                segmentation_checkout = checkout_time
        else:
            segmentation_checkin = checkin_time
            segmentation_checkout = checkout_time

        # Segment data using appropriate times
        sessions = self.segment_by_stay_sessions(
            df, segmentation_checkin, segmentation_checkout
        )

        # Fix session display times to show local hotel times
        if source_timezone and target_timezone and source_timezone != target_timezone:
            for session in sessions:
                # Convert session boundaries back to local time for display
                # Session times currently in target timezone, convert to local
                session["display_start_time"] = self._convert_session_time_to_local(
                    session["start_time"], target_timezone, source_timezone
                )
                session["display_end_time"] = self._convert_session_time_to_local(
                    session["end_time"], target_timezone, source_timezone
                )
        else:
            # No timezone conversion, use original times
            for session in sessions:
                session["display_start_time"] = session["start_time"]
                session["display_end_time"] = session["end_time"]

        # Generate export text
        export_date = datetime.now().strftime("%Y-%m-%d")
        content = self.generate_export_text(sessions, export_date, target_timezone)

        # Generate filename
        if not filename:
            if len(df["hotel_name"].unique()) == 1:
                hotel_name = df["hotel_name"].iloc[0]
                filename = f"{hotel_name}_對話分析報告_{export_date}.txt"
            else:
                filename = f"綜合對話分析報告_{export_date}.txt"

        return content, filename
