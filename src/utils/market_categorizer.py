"""Market categorizer for identifying crypto, entertainment, and other market types"""

import re
from typing import Dict, List, Optional, Set
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MarketCategory(Enum):
    """Market categories"""
    CRYPTO_BTC = "crypto_btc"
    CRYPTO_ETH = "crypto_eth"
    CRYPTO_SOL = "crypto_sol"
    CRYPTO_OTHER = "crypto_other"
    SPORTS = "sports"
    POLITICS = "politics"
    ENTERTAINMENT = "entertainment"
    FINANCE = "finance"
    OTHER = "other"


class MarketCategorizer:
    """Categorize and filter markets based on keywords and patterns"""

    # Crypto-related keywords
    CRYPTO_KEYWORDS = {
        'btc': MarketCategory.CRYPTO_BTC,
        'bitcoin': MarketCategory.CRYPTO_BTC,
        'eth': MarketCategory.CRYPTO_ETH,
        'ethereum': MarketCategory.CRYPTO_ETH,
        'sol': MarketCategory.CRYPTO_SOL,
        'solana': MarketCategory.CRYPTO_SOL,
    }

    # Entertainment keywords
    ENTERTAINMENT_KEYWORDS = [
        'movie', 'film', 'oscar', 'grammy', 'emmy', 'award',
        'celebrity', 'actor', 'actress', 'music', 'album',
        'box office', 'streaming', 'netflix', 'spotify',
        'taylor swift', 'beyonce', 'kanye'
    ]

    # Sports keywords
    SPORTS_KEYWORDS = [
        'nfl', 'nba', 'mlb', 'nhl', 'fifa', 'world cup',
        'super bowl', 'playoffs', 'championship', 'tournament',
        'olympic', 'football', 'basketball', 'baseball', 'soccer'
    ]

    # Politics keywords
    POLITICS_KEYWORDS = [
        'election', 'president', 'senate', 'congress', 'vote',
        'democrat', 'republican', 'policy', 'legislation',
        'biden', 'trump', 'governor', 'primary'
    ]

    def __init__(self):
        self.cache: Dict[str, MarketCategory] = {}

    def categorize(self, market: Dict) -> MarketCategory:
        """
        Categorize a market based on its question and description

        Args:
            market: Market data from Polymarket API

        Returns:
            MarketCategory enum value
        """
        market_id = market.get('id', '')

        # Check cache
        if market_id in self.cache:
            return self.cache[market_id]

        question = market.get('question', '').lower()
        description = market.get('description', '').lower()
        tags = [tag.lower() for tag in market.get('tags', [])]

        combined_text = f"{question} {description} {' '.join(tags)}"

        # Check crypto first (highest priority)
        for keyword, category in self.CRYPTO_KEYWORDS.items():
            if keyword in combined_text:
                self.cache[market_id] = category
                return category

        # Check other categories
        if any(kw in combined_text for kw in self.SPORTS_KEYWORDS):
            category = MarketCategory.SPORTS
        elif any(kw in combined_text for kw in self.POLITICS_KEYWORDS):
            category = MarketCategory.POLITICS
        elif any(kw in combined_text for kw in self.ENTERTAINMENT_KEYWORDS):
            category = MarketCategory.ENTERTAINMENT
        else:
            category = MarketCategory.OTHER

        self.cache[market_id] = category
        return category

    def is_crypto_market(self, market: Dict) -> bool:
        """Check if market is crypto-related"""
        category = self.categorize(market)
        return category in [
            MarketCategory.CRYPTO_BTC,
            MarketCategory.CRYPTO_ETH,
            MarketCategory.CRYPTO_SOL,
            MarketCategory.CRYPTO_OTHER
        ]

    def get_crypto_asset(self, market: Dict) -> Optional[str]:
        """
        Get the primary crypto asset for a market

        Returns:
            'BTC', 'ETH', 'SOL', or None
        """
        category = self.categorize(market)

        if category == MarketCategory.CRYPTO_BTC:
            return 'BTC'
        elif category == MarketCategory.CRYPTO_ETH:
            return 'ETH'
        elif category == MarketCategory.CRYPTO_SOL:
            return 'SOL'

        return None

    def filter_markets(self, markets: List[Dict],
                      categories: Optional[List[MarketCategory]] = None,
                      min_volume: float = 0) -> List[Dict]:
        """
        Filter markets by categories and volume

        Args:
            markets: List of markets to filter
            categories: List of categories to include (None = all)
            min_volume: Minimum volume threshold

        Returns:
            Filtered list of markets
        """
        filtered = []

        for market in markets:
            # Volume filter
            volume = market.get('volume', 0)
            if volume < min_volume:
                continue

            # Category filter
            if categories:
                market_category = self.categorize(market)
                if market_category not in categories:
                    continue

            filtered.append(market)

        logger.info(f"Filtered {len(markets)} markets to {len(filtered)} markets")
        return filtered

    def extract_price_target(self, market: Dict) -> Optional[float]:
        """
        Extract price target from market question (e.g., "Will BTC hit $100k?")

        Returns:
            Price target as float, or None if not found
        """
        question = market.get('question', '')

        # Pattern: $XXX, $X,XXX, $XX.XX, etc.
        price_patterns = [
            r'\$([0-9,]+\.?[0-9]*)[kK]',  # $100k format
            r'\$([0-9,]+\.?[0-9]*)',       # $100,000 format
        ]

        for pattern in price_patterns:
            match = re.search(pattern, question)
            if match:
                price_str = match.group(1).replace(',', '')

                # Handle k/K suffix
                if question[match.end()-1].lower() == 'k':
                    return float(price_str) * 1000
                else:
                    return float(price_str)

        return None

    def find_similar_markets(self, markets: List[Dict],
                           similarity_threshold: float = 0.7) -> List[List[Dict]]:
        """
        Find groups of similar markets (for cross-market arbitrage)

        Returns:
            List of market groups that are similar
        """
        from difflib import SequenceMatcher

        groups = []
        processed = set()

        for i, market1 in enumerate(markets):
            if market1['id'] in processed:
                continue

            group = [market1]
            question1 = market1.get('question', '').lower()

            for j, market2 in enumerate(markets[i+1:], start=i+1):
                if market2['id'] in processed:
                    continue

                question2 = market2.get('question', '').lower()

                # Calculate similarity
                similarity = SequenceMatcher(None, question1, question2).ratio()

                if similarity >= similarity_threshold:
                    group.append(market2)
                    processed.add(market2['id'])

            if len(group) > 1:
                groups.append(group)
                for m in group:
                    processed.add(m['id'])

        logger.info(f"Found {len(groups)} groups of similar markets")
        return groups

    def get_category_stats(self, markets: List[Dict]) -> Dict[str, int]:
        """Get distribution of markets across categories"""
        stats = {}

        for market in markets:
            category = self.categorize(market)
            category_name = category.value
            stats[category_name] = stats.get(category_name, 0) + 1

        return stats
