"""Sports-specific analytics including win streak analysis and momentum detection"""

import re
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Team:
    """Represents a team with performance data"""

    def __init__(self, name: str):
        self.name = name
        self.wins = 0
        self.losses = 0
        self.current_streak = 0  # Positive = win streak, negative = loss streak
        self.last_games = []  # Recent game results (1 = win, 0 = loss)

    def add_result(self, won: bool):
        """Add a game result"""
        if won:
            self.wins += 1
            self.current_streak = max(0, self.current_streak) + 1
        else:
            self.losses += 1
            self.current_streak = min(0, self.current_streak) - 1

        self.last_games.append(1 if won else 0)

    def get_win_rate(self) -> float:
        """Calculate win rate"""
        total = self.wins + self.losses
        return self.wins / total if total > 0 else 0.5

    def get_recent_form(self, games: int = 5) -> float:
        """Get recent form (last N games win rate)"""
        recent = self.last_games[-games:]
        return sum(recent) / len(recent) if recent else 0.5

    def has_hot_streak(self, min_streak: int = 3) -> bool:
        """Check if team has a hot winning streak"""
        return self.current_streak >= min_streak

    def has_cold_streak(self, min_streak: int = 3) -> bool:
        """Check if team has a cold losing streak"""
        return self.current_streak <= -min_streak


class SportsAnalytics:
    """
    Sports-specific market analytics

    Detects inefficiencies based on:
    - Win streaks (hot teams overvalued, cold teams undervalued)
    - Momentum shifts
    - Home/away advantages
    - Recent form vs. market odds
    """

    # Team name patterns for extraction
    TEAM_PATTERNS = [
        r'(\w+(?:\s+\w+)?)\s+(?:vs\.?|v\.?|@)\s+(\w+(?:\s+\w+)?)',  # Team1 vs Team2
        r'will\s+(\w+(?:\s+\w+)?)\s+(?:beat|defeat|win)',  # Will Team1 beat
        r'(\w+(?:\s+\w+)?)\s+(?:to|will)\s+win',  # Team1 to win
    ]

    # Sports leagues and competitions
    LEAGUES = [
        'nfl', 'nba', 'mlb', 'nhl', 'mls', 'epl', 'premier league',
        'champions league', 'fifa', 'world cup', 'ncaa', 'college',
        'uefa', 'la liga', 'serie a', 'bundesliga', 'ligue 1'
    ]

    def __init__(self, config: Dict = None):
        self.config = config or {}

        # Team database (would be populated from external API in production)
        self.teams: Dict[str, Team] = {}

        # Win streak thresholds
        self.hot_streak_threshold = self.config.get('hot_streak_threshold', 3)
        self.cold_streak_threshold = self.config.get('cold_streak_threshold', 3)

        # Overvaluation detection
        self.streak_overvalue_threshold = self.config.get('streak_overvalue_threshold', 0.15)

    def extract_teams(self, market: Dict) -> Optional[Tuple[str, str]]:
        """
        Extract team names from market question

        Returns:
            (team1, team2) or None
        """
        question = market.get('question', '')

        for pattern in self.TEAM_PATTERNS:
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                if len(match.groups()) >= 2:
                    return (match.group(1).strip(), match.group(2).strip())
                elif len(match.groups()) == 1:
                    return (match.group(1).strip(), None)

        return None

    def is_sports_market(self, market: Dict) -> bool:
        """Check if market is sports-related"""
        question = market.get('question', '').lower()
        description = market.get('description', '').lower()
        tags = [t.lower() for t in market.get('tags', [])]

        combined = f"{question} {description} {' '.join(tags)}"

        # Check for league mentions
        for league in self.LEAGUES:
            if league in combined:
                return True

        # Check for team patterns
        if self.extract_teams(market):
            return True

        # Check for sports keywords
        sports_keywords = [
            'game', 'match', 'score', 'goal', 'touchdown', 'point',
            'playoff', 'championship', 'final', 'quarter', 'half'
        ]

        return any(kw in combined for kw in sports_keywords)

    def detect_win_streak_inefficiency(self, market: Dict, prices: Dict,
                                      team_data: Dict = None) -> Optional[Dict]:
        """
        Detect if market is mispricing based on win streaks

        Theory:
        - Teams on hot streaks (3+ wins) are often OVERVALUED by public
        - Teams on cold streaks (3+ losses) are often UNDERVALUED
        - "Regression to the mean" creates value

        Args:
            market: Market data
            prices: Current prices
            team_data: Optional external team statistics

        Returns:
            Inefficiency data or None
        """
        teams = self.extract_teams(market)
        if not teams:
            return None

        team1_name, team2_name = teams

        # Try to get team data
        team1 = self.teams.get(team1_name) or (
            self._create_team_from_external(team1_name, team_data) if team_data else None
        )
        team2 = self.teams.get(team2_name) or (
            self._create_team_from_external(team2_name, team_data) if team_data else None
        ) if team2_name else None

        if not team1:
            return None

        # Analyze win streak bias
        inefficiency = {}

        # Check Team 1 for hot/cold streaks
        if team1.has_hot_streak(self.hot_streak_threshold):
            # Hot streak - likely overvalued
            if 'Yes' in prices:
                price = prices['Yes'].get('ask', 0)
                # Estimate "fair" value based on win rate (regressed to mean)
                win_rate = team1.get_win_rate()
                regressed_win_rate = (win_rate + 0.5) / 2  # Regress 50% to mean

                if price > regressed_win_rate + self.streak_overvalue_threshold:
                    inefficiency['type'] = 'hot_streak_overvalue'
                    inefficiency['team'] = team1_name
                    inefficiency['streak'] = team1.current_streak
                    inefficiency['market_price'] = price
                    inefficiency['fair_value'] = regressed_win_rate
                    inefficiency['edge'] = price - regressed_win_rate
                    inefficiency['recommendation'] = f"FADE {team1_name} (hot streak overvalued)"

        elif team1.has_cold_streak(self.cold_streak_threshold):
            # Cold streak - likely undervalued
            if 'Yes' in prices:
                price = prices['Yes'].get('ask', 0)
                win_rate = team1.get_win_rate()
                regressed_win_rate = (win_rate + 0.5) / 2

                if price < regressed_win_rate - self.streak_overvalue_threshold:
                    inefficiency['type'] = 'cold_streak_undervalue'
                    inefficiency['team'] = team1_name
                    inefficiency['streak'] = team1.current_streak
                    inefficiency['market_price'] = price
                    inefficiency['fair_value'] = regressed_win_rate
                    inefficiency['edge'] = regressed_win_rate - price
                    inefficiency['recommendation'] = f"BUY {team1_name} (cold streak undervalued)"

        # Check Team 2 if available
        if team2 and team2.has_hot_streak(self.hot_streak_threshold):
            if 'No' in prices:
                price = prices['No'].get('ask', 0)
                win_rate = team2.get_win_rate()
                regressed_win_rate = (win_rate + 0.5) / 2

                if price < regressed_win_rate - self.streak_overvalue_threshold:
                    inefficiency['type'] = 'hot_streak_overvalue_opponent'
                    inefficiency['team'] = team2_name
                    inefficiency['streak'] = team2.current_streak
                    inefficiency['recommendation'] = f"BUY against {team2_name} (opponent hot streak)"

        return inefficiency if inefficiency else None

    def _create_team_from_external(self, team_name: str, team_data: Dict) -> Optional[Team]:
        """Create team object from external data"""
        if team_name not in team_data:
            return None

        team = Team(team_name)
        data = team_data[team_name]

        team.wins = data.get('wins', 0)
        team.losses = data.get('losses', 0)
        team.current_streak = data.get('streak', 0)
        team.last_games = data.get('recent_results', [])

        self.teams[team_name] = team
        return team

    def analyze_momentum_shift(self, market: Dict, prices: Dict,
                               historical_prices: List[Dict]) -> Optional[Dict]:
        """
        Detect momentum shifts in market prices

        Sharp price movements in sports markets can indicate:
        - Injury news
        - Lineup changes
        - Weather conditions
        - Public betting patterns

        Args:
            market: Market data
            prices: Current prices
            historical_prices: List of historical price snapshots

        Returns:
            Momentum analysis
        """
        if len(historical_prices) < 3:
            return None

        # Calculate price velocity and acceleration
        if 'Yes' not in prices:
            return None

        current_price = prices['Yes'].get('mid', 0)

        # Get last 3 prices
        recent_prices = [p.get('Yes', {}).get('mid', 0) for p in historical_prices[-3:]]
        recent_prices.append(current_price)

        # Calculate velocity (price change rate)
        velocities = []
        for i in range(1, len(recent_prices)):
            velocity = recent_prices[i] - recent_prices[i-1]
            velocities.append(velocity)

        avg_velocity = sum(velocities) / len(velocities)

        # Strong momentum if velocity > 5% per update
        if abs(avg_velocity) > 0.05:
            return {
                'type': 'momentum_shift',
                'direction': 'bullish' if avg_velocity > 0 else 'bearish',
                'velocity': avg_velocity,
                'current_price': current_price,
                'recommendation': 'Ride momentum' if abs(avg_velocity) > 0.08 else 'Monitor'
            }

        return None

    def get_team_stats(self, team_name: str) -> Optional[Dict]:
        """Get statistics for a team"""
        team = self.teams.get(team_name)
        if not team:
            return None

        return {
            'name': team.name,
            'wins': team.wins,
            'losses': team.losses,
            'win_rate': team.get_win_rate(),
            'streak': team.current_streak,
            'recent_form': team.get_recent_form(),
            'is_hot': team.has_hot_streak(),
            'is_cold': team.has_cold_streak()
        }

    def add_team_result(self, team_name: str, won: bool):
        """Add a game result for a team"""
        if team_name not in self.teams:
            self.teams[team_name] = Team(team_name)

        self.teams[team_name].add_result(won)
