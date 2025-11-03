"""
Export manager module for Smart Speaker Conversation Analysis Platform
Handles conversation export with stay session segmentation
"""

import json
import logging
from datetime import datetime, time, timedelta
from typing import Dict, List, Tuple

import pandas as pd

# Setup logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ExportManager:
    """Manage data export with intelligent stay session segmentation"""

    def segment_by_stay_sessions(
        self, df: pd.DataFrame, checkin_time_str: str, checkout_time_str: str, gap_period_mode: str = "合併到下一個住宿時段"
    ) -> List[Dict]:
        """
        Segment conversations by stay sessions

        Args:
            df: Filtered DataFrame with conversation data
            checkin_time_str: Standard check-in time (e.g., "14:00")
            checkout_time_str: Standard check-out time (e.g., "11:00")
            gap_period_mode: How to handle gap period conversations (between checkout and checkin)
                - "合併到下一個住宿時段": Merge into next stay session (default)
                - "單獨標記為「空檔期」時段": Mark as separate gap period sessions
                - "不包含空檔期對話": Exclude gap period conversations

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
                group_df, hotel, room, checkin_time, checkout_time, gap_period_mode
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
        gap_period_mode: str = "合併到下一個住宿時段",
    ) -> List[Dict]:
        """
        Segment conversations for a single room into stay sessions

        Args:
            room_df: DataFrame of conversations for one room
            hotel: Hotel name
            room: Room name
            checkin_time: Standard check-in time
            checkout_time: Standard check-out time
            gap_period_mode: How to handle gap period conversations

        Returns:
            List of stay session dictionaries
        """
        # For mode 2, we need to track gap period sessions separately
        if gap_period_mode == "單獨標記為「空檔期」時段":
            return self._segment_with_separate_gaps(
                room_df, hotel, room, checkin_time, checkout_time
            )

        # For modes 1 and 3, use the simpler approach
        sessions = []
        current_session = None
        current_conversations = []

        for _, row in room_df.iterrows():
            timestamp = row["request_timestamp"]

            # Check if conversation is in gap period
            is_gap = self._is_gap_period(timestamp, checkin_time, checkout_time)

            # Mode 3: Skip gap period conversations
            if gap_period_mode == "不包含空檔期對話" and is_gap:
                continue

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

    def _segment_with_separate_gaps(
        self,
        room_df: pd.DataFrame,
        hotel: str,
        room: str,
        checkin_time: time,
        checkout_time: time,
    ) -> List[Dict]:
        """
        Segment conversations with gap periods as separate sessions

        Args:
            room_df: DataFrame of conversations for one room
            hotel: Hotel name
            room: Room name
            checkin_time: Standard check-in time
            checkout_time: Standard check-out time

        Returns:
            List of stay session dictionaries including gap period sessions
        """
        sessions = []

        for _, row in room_df.iterrows():
            timestamp = row["request_timestamp"]
            is_gap = self._is_gap_period(timestamp, checkin_time, checkout_time)

            if is_gap:
                # Create gap period session for this conversation
                gap_start, gap_end = self._get_gap_period_boundaries(
                    timestamp, checkin_time, checkout_time
                )
                session_key = (gap_start, gap_end, True)  # True = is_gap_period
            else:
                # Create regular stay session
                session_bounds = self._create_session_boundaries(
                    timestamp, checkin_time, checkout_time
                )
                session_key = (session_bounds["start"], session_bounds["end"], False)

            # Find or create session
            found = False
            for session in sessions:
                if (session["start_time"], session["end_time"], session.get("is_gap_period", False)) == session_key:
                    session["conversations"].append(row)
                    found = True
                    break

            if not found:
                sessions.append({
                    "hotel": hotel,
                    "room": room,
                    "start_time": session_key[0],
                    "end_time": session_key[1],
                    "conversations": [row],
                    "is_gap_period": session_key[2],
                })

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
        elif checkout_time <= checkin_time and conversation_time > checkout_time:
            # Conversation is after checkout but before next checkin (gap period)
            # This belongs to the session starting today
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

    def _is_gap_period(self, timestamp: datetime, checkin_time: time, checkout_time: time) -> bool:
        """
        Check if a timestamp is in the gap period between checkout and checkin

        Args:
            timestamp: Conversation timestamp
            checkin_time: Standard check-in time
            checkout_time: Standard check-out time

        Returns:
            True if timestamp is in gap period, False otherwise
        """
        conversation_time = timestamp.time()

        # Gap period exists when checkout < checkin (e.g., 11:00 checkout, 14:00 checkin)
        # Conversation is in gap if its time is between checkout and checkin
        if checkout_time < checkin_time:
            return checkout_time <= conversation_time < checkin_time
        else:
            # No gap period if checkout >= checkin (unusual case)
            return False

    def _get_next_checkin_datetime(self, checkout_datetime: datetime, checkin_time: time) -> datetime:
        """
        Calculate the next check-in datetime after a checkout

        Args:
            checkout_datetime: Checkout datetime
            checkin_time: Standard check-in time

        Returns:
            Next check-in datetime
        """
        # Same day if checkin time is after checkout time
        if checkin_time > checkout_datetime.time():
            return datetime.combine(checkout_datetime.date(), checkin_time)
        else:
            # Next day if checkin time is before checkout time
            return datetime.combine(checkout_datetime.date() + timedelta(days=1), checkin_time)

    def _get_gap_period_boundaries(
        self, timestamp: datetime, checkin_time: time, checkout_time: time
    ) -> Tuple[datetime, datetime]:
        """
        Calculate the gap period boundaries for a given timestamp

        Args:
            timestamp: A conversation timestamp in the gap period
            checkin_time: Standard check-in time
            checkout_time: Standard check-out time

        Returns:
            Tuple of (gap_start_datetime, gap_end_datetime)
        """
        # Gap period is always on the same day as the conversation
        # Gap starts at checkout time and ends at checkin time
        conversation_date = timestamp.date()

        gap_start = datetime.combine(conversation_date, checkout_time)
        gap_end = datetime.combine(conversation_date, checkin_time)

        return gap_start, gap_end

    def _extract_alarm_time(self, conv: pd.Series) -> str:
        """
        Extract alarm time information from conversation data

        Args:
            conv: Conversation row as pandas Series

        Returns:
            Formatted alarm time string or empty string if not applicable
        """
        try:
            # Check if this is an alarm intent
            user_intent = conv.get("user_intent", "").lower()
            logger.debug(f"Step 1: user_intent = '{user_intent}'")
            if user_intent != "alarm":
                logger.debug("Not an alarm intent, returning empty")
                return ""

            # Get data field
            data_field = conv.get("data", None)
            logger.debug(f"Step 2: data_field exists = {data_field is not None}, is_na = {pd.isna(data_field)}")
            if pd.isna(data_field) or not data_field:
                logger.debug("data_field is NA or empty")
                return ""

            # Parse data JSON
            logger.debug(f"Step 3: data_field type = {type(data_field)}")
            if isinstance(data_field, str):
                try:
                    data_json = json.loads(data_field)
                    logger.debug(f"Step 3a: Successfully parsed data_field as JSON, result type = {type(data_json)}")
                except (json.JSONDecodeError, ValueError) as e:
                    logger.debug(f"Step 3a: Failed to parse data_field: {e}")
                    return ""
            elif isinstance(data_field, dict):
                data_json = data_field
                logger.debug("Step 3b: data_field is already a dict")
            elif isinstance(data_field, list):
                data_json = data_field
                logger.debug("Step 3c: data_field is already a list")
            else:
                logger.debug(f"Step 3d: data_field is unexpected type: {type(data_field)}")
                return ""

            # If data_json is a list, extract the first element
            if isinstance(data_json, list):
                logger.debug(f"Step 4a: data_json is a list with {len(data_json)} elements")
                if len(data_json) == 0:
                    logger.debug("Step 4b: data_json is empty list")
                    return ""
                # Take the first element
                data_json = data_json[0]
                logger.debug(f"Step 4c: Extracted first element, type = {type(data_json)}")

            # Check if data_json is a dict
            if not isinstance(data_json, dict):
                logger.debug(f"Step 5: data_json is {type(data_json)}, not a dict. Skipping.")
                return ""

            # Check for uni_df_datetime
            uni_df_datetime = data_json.get("uni_df_datetime", None)
            logger.debug(f"Step 6: uni_df_datetime exists = {uni_df_datetime is not None}, type = {type(uni_df_datetime) if uni_df_datetime else 'N/A'}")
            if not uni_df_datetime:
                logger.debug("uni_df_datetime not found")
                return ""

            # Parse uni_df_datetime if it's a string
            if isinstance(uni_df_datetime, str):
                logger.debug("Step 7: uni_df_datetime is string, parsing...")
                try:
                    uni_df_datetime = json.loads(uni_df_datetime)
                    logger.debug("Step 7a: Successfully parsed uni_df_datetime")
                except (json.JSONDecodeError, ValueError) as e:
                    logger.debug(f"Step 7a: Failed to parse uni_df_datetime: {e}")
                    return ""

            if not isinstance(uni_df_datetime, dict):
                logger.debug("Step 8: uni_df_datetime is not a dict after parsing")
                return ""

            # Get startDateTime and endDateTime
            start_datetime = uni_df_datetime.get("startDateTime", None)
            end_datetime = uni_df_datetime.get("endDateTime", None)
            logger.debug(f"Step 9: startDateTime = {start_datetime}, endDateTime = {end_datetime}")

            # Only show if startDateTime equals endDateTime
            if not start_datetime or not end_datetime or start_datetime != end_datetime:
                logger.debug("Step 10: Times don't match or are empty")
                return ""

            # Parse and format the datetime
            # Expected format: ISO 8601 or similar
            try:
                if isinstance(start_datetime, str):
                    logger.debug(f"Step 11: Parsing datetime string: {start_datetime}")
                    dt = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M")
                    logger.info(f"SUCCESS! Extracted alarm time: {formatted_time}")
                    return f" alarm_entity:({formatted_time})"
                else:
                    logger.debug("Step 11: start_datetime is not a string")
                    return ""
            except (ValueError, AttributeError) as e:
                logger.debug(f"Step 11: Failed to parse datetime: {e}")
                return ""

        except Exception as e:
            logger.exception(f"Exception in _extract_alarm_time: {type(e).__name__}: {e}")
            return ""

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

        # Sort sessions by start_time first, then by room name
        sorted_sessions = sorted(sessions, key=lambda s: (s["start_time"], s["room"]))

        # Header
        lines = [
            "智能音箱對話分析報告",
            f"導出日期：{export_date}{timezone_display}",
            f"總共 {len(sorted_sessions)} 個住宿時段",
            "=" * 80,
            "",
        ]

        # Add each session as a separate report section
        for i, session in enumerate(sorted_sessions, 1):
            hotel = session["hotel"]
            room = session["room"]
            is_gap = session.get("is_gap_period", False)

            # Use display times if available (for timezone-corrected display)
            if "display_start_time" in session and "display_end_time" in session:
                start_time = session["display_start_time"].strftime("%Y-%m-%d %H:%M")
                end_time = session["display_end_time"].strftime("%Y-%m-%d %H:%M")
            else:
                start_time = session["start_time"].strftime("%Y-%m-%d %H:%M")
                end_time = session["end_time"].strftime("%Y-%m-%d %H:%M")

            if is_gap:
                lines.append(f"## 用戶體驗報告 ({hotel} - {room}) [空檔期]")
                lines.append(f"### 空檔期間（退房後到入住前）：{start_time} ~ {end_time}")
            else:
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

                # Extract alarm time information if applicable
                logger.debug(f"Processing conversation: intent={conv.get('user_intent', 'N/A')}, query={user_query[:50] if user_query else 'N/A'}")
                alarm_time_info = self._extract_alarm_time(conv)
                logger.debug(f"Alarm time info result: '{alarm_time_info}'")

                lines.append(f"[{timestamp}], (ID: {conv_id})")
                lines.append(f"user：{user_query}")
                lines.append(f"chatbot: {chatbot_response}{alarm_time_info} (思考時間:{timecost:.2f}s)")
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
        gap_period_mode: str = "合併到下一個住宿時段",
    ) -> Tuple[str, str]:
        """
        Complete export workflow

        Args:
            df: Filtered DataFrame (may be timezone-converted)
            checkin_time: Check-in time string in target timezone (e.g., "14:00")
            checkout_time: Check-out time string in target timezone (e.g., "11:00")
            filename: Optional filename
            target_timezone: Target timezone for display (e.g., 'UTC', 'Asia/Taipei')
            gap_period_mode: How to handle gap period conversations

        Returns:
            Tuple of (content: str, filename: str)
        """
        # Use check-in/check-out times directly as they are already in target timezone
        segmentation_checkin = checkin_time
        segmentation_checkout = checkout_time

        # Segment data using appropriate times
        sessions = self.segment_by_stay_sessions(
            df, segmentation_checkin, segmentation_checkout, gap_period_mode
        )

        # Set display times directly from session times
        # Since check-in/check-out times are already in target timezone,
        # session boundaries are also in the correct timezone
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
