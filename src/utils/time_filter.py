"""Time-based market filtering for short-duration opportunities"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class TimeInterval:
    """Market time intervals"""
    MINUTES_15 = "15min"
    MINUTES_30 = "30min"
    HOUR_1 = "1hour"
    HOURS_2 = "2hours"
    HOURS_4 = "4hours"
    DAY_1 = "1day"
    WEEK_1 = "1week"
    MONTH_1 = "1month"


class TimeBasedFilter:
    """Filter markets based on time to resolution"""

    # Pattern matching for time-based questions
    TIME_PATTERNS = [
        # Specific times
        (r'by (\d{1,2}):(\d{2})', 'specific_time'),
        (r'at (\d{1,2}):(\d{2})', 'specific_time'),

        # Minutes
        (r'in (\d+) minutes?', 'minutes'),
        (r'next (\d+) minutes?', 'minutes'),
        (r'within (\d+) minutes?', 'minutes'),

        # Hours
        (r'in (\d+) hours?', 'hours'),
        (r'next (\d+) hours?', 'hours'),
        (r'within (\d+) hours?', 'hours'),

        # Half hour, quarter
        (r'half hour', 'half_hour'),
        (r'30 min', 'half_hour'),
        (r'quarter', 'quarter_hour'),
        (r'15 min', 'quarter_hour'),

        # Dates
        (r'by (\d{4})-(\d{2})-(\d{2})', 'date'),
        (r'by (\w+) (\d{1,2})', 'date_text'),

        # Game periods/quarters
        (r'(first|second|third|fourth) quarter', 'game_quarter'),
        (r'(1st|2nd|3rd|4th) quarter', 'game_quarter'),
        (r'first half', 'game_half'),
        (r'halftime', 'game_half'),
    ]

    def __init__(self, config: Dict = None):
        self.config = config or {}

        # Time thresholds
        self.max_minutes = self.config.get('max_minutes', 60)  # Default 1 hour
        self.min_minutes = self.config.get('min_minutes', 5)   # Minimum 5 minutes

    def extract_time_to_resolution(self, market: Dict) -> Optional[int]:
        """
        Extract estimated time to resolution in minutes

        Returns:
            Minutes until resolution, or None if unknown
        """
        question = market.get('question', '').lower()
        description = market.get('description', '').lower()

        # Check end_date if available
        end_date_str = market.get('end_date') or market.get('endDate')
        if end_date_str:
            try:
                # Try parsing various date formats
                for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                    try:
                        end_date = datetime.strptime(end_date_str[:19], fmt)
                        now = datetime.now()
                        diff = end_date - now
                        return int(diff.total_seconds() / 60)
                    except ValueError:
                        continue
            except Exception as e:
                logger.debug(f"Error parsing end_date: {e}")

        # Pattern matching
        combined_text = f"{question} {description}"

        for pattern, pattern_type in self.TIME_PATTERNS:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                return self._calculate_minutes(match, pattern_type, combined_text)

        return None

    def _calculate_minutes(self, match, pattern_type: str, text: str) -> Optional[int]:
        """Calculate minutes from regex match"""
        try:
            if pattern_type == 'specific_time':
                # Calculate time until specific hour:minute
                hour = int(match.group(1))
                minute = int(match.group(2))

                now = datetime.now()
                target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

                # If time has passed today, assume tomorrow
                if target < now:
                    target += timedelta(days=1)

                diff = target - now
                return int(diff.total_seconds() / 60)

            elif pattern_type == 'minutes':
                return int(match.group(1))

            elif pattern_type == 'hours':
                return int(match.group(1)) * 60

            elif pattern_type == 'half_hour':
                return 30

            elif pattern_type == 'quarter_hour':
                return 15

            elif pattern_type == 'game_quarter':
                # Typical quarter is 12-15 minutes
                return 15

            elif pattern_type == 'game_half':
                # Half is ~45-60 minutes
                return 45

            elif pattern_type == 'date':
                year = int(match.group(1))
                month = int(match.group(2))
                day = int(match.group(3))

                target = datetime(year, month, day)
                now = datetime.now()
                diff = target - now
                return int(diff.total_seconds() / 60)

        except Exception as e:
            logger.debug(f"Error calculating minutes: {e}")
            return None

        return None

    def categorize_interval(self, minutes: int) -> str:
        """Categorize time interval"""
        if minutes <= 15:
            return TimeInterval.MINUTES_15
        elif minutes <= 30:
            return TimeInterval.MINUTES_30
        elif minutes <= 60:
            return TimeInterval.HOUR_1
        elif minutes <= 120:
            return TimeInterval.HOURS_2
        elif minutes <= 240:
            return TimeInterval.HOURS_4
        elif minutes <= 1440:
            return TimeInterval.DAY_1
        elif minutes <= 10080:
            return TimeInterval.WEEK_1
        else:
            return TimeInterval.MONTH_1

    def is_short_term(self, market: Dict) -> bool:
        """Check if market is short-term (within max_minutes threshold)"""
        minutes = self.extract_time_to_resolution(market)

        if minutes is None:
            return False

        return self.min_minutes <= minutes <= self.max_minutes

    def filter_short_term_markets(self, markets: List[Dict]) -> List[Dict]:
        """
        Filter markets to only short-term ones

        Returns:
            List of markets resolving within max_minutes
        """
        short_term = []

        for market in markets:
            if self.is_short_term(market):
                minutes = self.extract_time_to_resolution(market)
                market['_time_to_resolution'] = minutes
                market['_time_interval'] = self.categorize_interval(minutes)
                short_term.append(market)

        logger.info(f"Filtered {len(markets)} markets to {len(short_term)} short-term markets (<{self.max_minutes} min)")

        return short_term

    def get_urgency_score(self, market: Dict) -> float:
        """
        Calculate urgency score (0-1) based on time to resolution

        Lower time = higher urgency
        """
        minutes = self.extract_time_to_resolution(market)

        if minutes is None:
            return 0.0

        # Normalize: 5 min = 1.0, max_minutes = 0.1
        if minutes <= self.min_minutes:
            return 1.0

        urgency = 1.0 - ((minutes - self.min_minutes) / (self.max_minutes - self.min_minutes)) * 0.9
        return max(0.1, min(1.0, urgency))

    def get_time_distribution(self, markets: List[Dict]) -> Dict[str, int]:
        """Get distribution of markets across time intervals"""
        distribution = {}

        for market in markets:
            minutes = self.extract_time_to_resolution(market)
            if minutes:
                interval = self.categorize_interval(minutes)
                distribution[interval] = distribution.get(interval, 0) + 1

        return distribution
