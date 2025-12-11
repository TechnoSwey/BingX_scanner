import ccxt.async_support as ccxt
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class DataFetcher:
    def __init__(self, config):
        self.config = config
        self.exchange = ccxt.bingx({
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'}
        })
        self.pairs_cache = None
        self.pairs_cache_time = None
        self.semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_REQUESTS)
        
    async def initialize(self):
        try:
            await self.exchange.load_markets()
            logger.info("Exchange initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize exchange: {e}")
            raise
    
    async def close(self):
        await self.exchange.close()
    
    async def get_liquid_pairs(self) -> List[str]:
        if (self.pairs_cache and self.pairs_cache_time and 
            datetime.now() - self.pairs_cache_time < timedelta(hours=self.config.PAIRS_CACHE_HOURS)):
            logger.info(f"Using cached pairs: {len(self.pairs_cache)} pairs")
            return self.pairs_cache
        
        try:
            markets = await self.exchange.fetch_markets()
            
            usdt_futures = [
                m['symbol'] for m in markets 
                if m.get('type') == 'swap' and 
                   m.get('quote') == 'USDT' and 
                   m.get('active', True)
            ]
            
            logger.info(f"Found {len(usdt_futures)} USDT-M futures pairs")
            
            liquid_pairs = []
            tasks = []
            
            for symbol in usdt_futures:
                tasks.append(self._check_liquidity(symbol))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for symbol, is_liquid in zip(usdt_futures, results):
                if is_liquid and not isinstance(is_liquid, Exception):
                    liquid_pairs.append(symbol)
            
            logger.info(f"Filtered to {len(liquid_pairs)} liquid pairs (volume > {self.config.MIN_VOLUME_USDT/1e6}M USDT)")
            
            self.pairs_cache = liquid_pairs
            self.pairs_cache_time = datetime.now()
            
            return liquid_pairs
            
        except Exception as e:
            logger.error(f"Error fetching liquid pairs: {e}")
            return []
    
    async def _check_liquidity(self, symbol: str) -> bool:
        async with self.semaphore:
            try:
                ticker = await self.exchange.fetch_ticker(symbol)
                volume_usdt = ticker.get('quoteVolume', 0)
                return volume_usdt >= self.config.MIN_VOLUME_USDT
            except Exception as e:
                logger.warning(f"Error checking liquidity for {symbol}: {e}")
                return False
    
    async def fetch_ohlcv_data(self, symbol: str, timeframe: str, limit: int) -> Optional[list]:
        async with self.semaphore:
            try:
                await asyncio.sleep(0.1)
                ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
                return ohlcv
            except Exception as e:
                logger.warning(f"Error fetching OHLCV for {symbol} {timeframe}: {e}")
                return None
    
    async def fetch_orderbook(self, symbol: str, limit: int = 20) -> Optional[Dict]:
        async with self.semaphore:
            try:
                await asyncio.sleep(0.1)
                orderbook = await self.exchange.fetch_order_book(symbol, limit=limit)
                return orderbook
            except Exception as e:
                logger.warning(f"Error fetching orderbook for {symbol}: {e}")
                return None
    
    async def fetch_symbol_data(self, symbol: str) -> Optional[Dict]:
        try:
            ohlcv_5m_task = self.fetch_ohlcv_data(symbol, '5m', 100)
            ohlcv_1m_task = self.fetch_ohlcv_data(symbol, '1m', 20)
            orderbook_task = self.fetch_orderbook(symbol)
            
            ohlcv_5m, ohlcv_1m, orderbook = await asyncio.gather(
                ohlcv_5m_task, ohlcv_1m_task, orderbook_task
            )
            
            if not ohlcv_5m or not ohlcv_1m:
                return None
            
            return {
                'symbol': symbol,
                'ohlcv_5m': ohlcv_5m,
                'ohlcv_1m': ohlcv_1m,
                'orderbook': orderbook
            }
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None
