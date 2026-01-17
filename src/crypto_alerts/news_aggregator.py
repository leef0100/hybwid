"""News Aggregator for crypto, political, and market news"""

import aiohttp
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class NewsAggregator:
    """Aggregates news from various crypto and mainstream sources"""

    def __init__(self, max_items: int = 10):
        """
        Args:
            max_items: Maximum number of news items to return per category
        """
        self.max_items = max_items
        self.session: Optional[aiohttp.ClientSession] = None

        # CryptoPanic API for crypto news
        self.cryptopanic_url = "https://cryptopanic.com/api/v1/posts/"

        # NewsAPI-like sources (using free RSS/JSON endpoints)
        self.news_sources = {
            'crypto': [
                'https://cryptopanic.com/api/v1/posts/',
            ],
            'general': []
        }

    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def _fetch_cryptopanic_news(self, filter_type: str = 'trending') -> List[Dict]:
        """Fetch news from CryptoPanic (free tier)"""
        await self._ensure_session()

        params = {
            'auth_token': 'free',  # Free tier
            'filter': filter_type,
            'kind': 'news'
        }

        try:
            async with self.session.get(self.cryptopanic_url, params=params, ssl=False) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get('results', [])

                    news_items = []
                    for item in results[:self.max_items]:
                        news_items.append({
                            'title': item.get('title', ''),
                            'url': item.get('url', ''),
                            'source': item.get('source', {}).get('title', 'Unknown'),
                            'published_at': item.get('published_at', ''),
                            'sentiment': item.get('votes', {}).get('kind', 'neutral'),
                            'currencies': [c.get('code') for c in item.get('currencies', [])],
                            'category': 'crypto'
                        })

                    logger.info(f"Fetched {len(news_items)} crypto news items")
                    return news_items
                else:
                    logger.error(f"CryptoPanic API error: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching CryptoPanic news: {e}")
            return []

    async def _fetch_coinglass_news(self) -> List[Dict]:
        """Fetch market data updates from Coinglass"""
        # Note: Coinglass doesn't have a dedicated news endpoint
        # This is a placeholder for market data summaries
        news_items = []

        try:
            # Could integrate Coinglass market data as "news items"
            # For now, returning empty list
            logger.info("Coinglass news integration placeholder")
        except Exception as e:
            logger.error(f"Error fetching Coinglass news: {e}")

        return news_items

    async def _fetch_coindesk_rss(self) -> List[Dict]:
        """Fetch news from CoinDesk RSS feed"""
        await self._ensure_session()

        url = "https://www.coindesk.com/arc/outboundfeeds/rss/"

        try:
            async with self.session.get(url, ssl=False) as response:
                if response.status == 200:
                    # Parse RSS feed
                    import xml.etree.ElementTree as ET

                    content = await response.text()
                    root = ET.fromstring(content)

                    news_items = []
                    for item in root.findall('.//item')[:self.max_items]:
                        title = item.find('title')
                        link = item.find('link')
                        pub_date = item.find('pubDate')
                        description = item.find('description')

                        news_items.append({
                            'title': title.text if title is not None else '',
                            'url': link.text if link is not None else '',
                            'source': 'CoinDesk',
                            'published_at': pub_date.text if pub_date is not None else '',
                            'description': description.text if description is not None else '',
                            'category': 'crypto'
                        })

                    logger.info(f"Fetched {len(news_items)} CoinDesk news items")
                    return news_items
                else:
                    logger.warning(f"CoinDesk RSS error: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching CoinDesk RSS: {e}")
            return []

    async def _fetch_cointelegraph_rss(self) -> List[Dict]:
        """Fetch news from Cointelegraph RSS feed"""
        await self._ensure_session()

        url = "https://cointelegraph.com/rss"

        try:
            async with self.session.get(url, ssl=False) as response:
                if response.status == 200:
                    import xml.etree.ElementTree as ET

                    content = await response.text()
                    root = ET.fromstring(content)

                    news_items = []
                    for item in root.findall('.//item')[:self.max_items]:
                        title = item.find('title')
                        link = item.find('link')
                        pub_date = item.find('pubDate')
                        description = item.find('description')

                        news_items.append({
                            'title': title.text if title is not None else '',
                            'url': link.text if link is not None else '',
                            'source': 'Cointelegraph',
                            'published_at': pub_date.text if pub_date is not None else '',
                            'description': description.text if description is not None else '',
                            'category': 'crypto'
                        })

                    logger.info(f"Fetched {len(news_items)} Cointelegraph news items")
                    return news_items
                else:
                    logger.warning(f"Cointelegraph RSS error: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching Cointelegraph RSS: {e}")
            return []

    async def get_crypto_news(self, symbols: Optional[List[str]] = None) -> List[Dict]:
        """
        Get crypto news, optionally filtered by symbols

        Args:
            symbols: List of symbols to filter by (e.g., ['BTC', 'ETH', 'SOL'])
        """
        all_news = []

        # Fetch from multiple sources
        cryptopanic_news = await self._fetch_cryptopanic_news()
        all_news.extend(cryptopanic_news)

        # Try RSS feeds as backup
        if len(all_news) < 5:
            coindesk_news = await self._fetch_coindesk_rss()
            all_news.extend(coindesk_news)

        if len(all_news) < 5:
            cointelegraph_news = await self._fetch_cointelegraph_rss()
            all_news.extend(cointelegraph_news)

        # Filter by symbols if provided
        if symbols:
            filtered_news = []
            for item in all_news:
                # Check if any of the target symbols are mentioned
                currencies = item.get('currencies', [])
                title_lower = item.get('title', '').lower()

                if any(symbol in currencies or symbol.lower() in title_lower for symbol in symbols):
                    filtered_news.append(item)

            # If filtered list is too small, add some general news
            if len(filtered_news) < self.max_items // 2:
                filtered_news.extend(all_news[:self.max_items - len(filtered_news)])

            return filtered_news[:self.max_items]

        return all_news[:self.max_items]

    async def get_political_news(self, crypto_related: bool = True) -> List[Dict]:
        """
        Get political news relevant to crypto

        Args:
            crypto_related: If True, focus on crypto-related political news
        """
        # Fetch crypto news and filter for political/regulatory topics
        crypto_news = await self._fetch_cryptopanic_news(filter_type='news')

        political_keywords = [
            'regulation', 'sec', 'government', 'law', 'policy', 'ban',
            'congress', 'senate', 'federal', 'regulatory', 'legal',
            'whitehouse', 'president', 'treasury', 'fed', 'central bank'
        ]

        political_news = []
        for item in crypto_news:
            title_lower = item.get('title', '').lower()
            if any(keyword in title_lower for keyword in political_keywords):
                item['category'] = 'political'
                political_news.append(item)

        logger.info(f"Found {len(political_news)} political news items")
        return political_news[:self.max_items]

    async def get_market_updates(self, symbols: Optional[List[str]] = None) -> List[Dict]:
        """
        Get market-specific updates and analysis

        Args:
            symbols: List of symbols to get updates for
        """
        # Fetch trending/important market news
        market_news = await self._fetch_cryptopanic_news(filter_type='important')

        # Filter for market-specific keywords
        market_keywords = [
            'price', 'surge', 'crash', 'rally', 'dip', 'ath', 'all-time high',
            'volume', 'trading', 'market', 'bullish', 'bearish', 'trend',
            'liquidation', 'futures', 'options', 'derivatives'
        ]

        filtered_news = []
        for item in market_news:
            title_lower = item.get('title', '').lower()
            if any(keyword in title_lower for keyword in market_keywords):
                item['category'] = 'market'
                filtered_news.append(item)

        # Filter by symbols if provided
        if symbols:
            symbol_news = []
            for item in filtered_news:
                currencies = item.get('currencies', [])
                title_lower = item.get('title', '').lower()

                if any(symbol in currencies or symbol.lower() in title_lower for symbol in symbols):
                    symbol_news.append(item)

            if symbol_news:
                filtered_news = symbol_news

        logger.info(f"Found {len(filtered_news)} market update items")
        return filtered_news[:self.max_items]

    async def get_all_news(self, symbols: Optional[List[str]] = None) -> Dict[str, List[Dict]]:
        """
        Get all news categories

        Returns:
            Dict with categories: crypto, political, market
        """
        crypto_news = await self.get_crypto_news(symbols)
        political_news = await self.get_political_news()
        market_updates = await self.get_market_updates(symbols)

        return {
            'crypto': crypto_news,
            'political': political_news,
            'market': market_updates,
            'total_items': len(crypto_news) + len(political_news) + len(market_updates)
        }

    def format_news_item(self, item: Dict) -> str:
        """Format a news item for display"""
        title = item.get('title', 'No title')
        source = item.get('source', 'Unknown')
        url = item.get('url', '')
        category = item.get('category', 'general')

        # Add sentiment indicator if available
        sentiment = item.get('sentiment', '')
        sentiment_indicator = ''
        if sentiment == 'positive':
            sentiment_indicator = '📈'
        elif sentiment == 'negative':
            sentiment_indicator = '📉'

        return f"{sentiment_indicator} [{source}] {title}\n   {url}"

    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
