import pandas as pd
import numpy as np
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
from typing import Dict, Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)

class TechnicalAnalyzer:
    def __init__(self, config):
        self.config = config
    
    def analyze(self, data: Dict) -> Optional[Dict]:
        try:
            symbol = data['symbol']
            
            df_5m = self._ohlcv_to_df(data['ohlcv_5m'])
            df_1m = self._ohlcv_to_df(data['ohlcv_1m'])
            
            if df_5m is None or df_1m is None:
                return None
            
            indicators_5m = self._calculate_indicators(df_5m)
            indicators_1m = self._calculate_indicators(df_1m)
            
            patterns = self._detect_patterns(df_5m)
            
            sr_levels = self._find_sr_levels(data.get('orderbook'), df_5m['close'].iloc[-1])
            
            current_price = df_5m['close'].iloc[-1]
            current_volume = df_5m['volume'].iloc[-1]
            
            analysis = {
                'symbol': symbol,
                'price': current_price,
                'timestamp': df_5m.index[-1],
                'indicators_5m': indicators_5m,
                'indicators_1m': indicators_1m,
                'patterns': patterns,
                'sr_levels': sr_levels,
                'volume': current_volume,
                'df_5m': df_5m,
                'df_1m': df_1m
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in technical analysis for {data.get('symbol')}: {e}")
            return None
    
    def _ohlcv_to_df(self, ohlcv: list) -> Optional[pd.DataFrame]:
        try:
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            return df
        except Exception as e:
            logger.error(f"Error converting OHLCV to DataFrame: {e}")
            return None
    
    def _calculate_indicators(self, df: pd.DataFrame) -> Dict:
        try:
            ema9 = EMAIndicator(df['close'], window=self.config.EMA_FAST).ema_indicator()
            ema21 = EMAIndicator(df['close'], window=self.config.EMA_MEDIUM).ema_indicator()
            ema50 = EMAIndicator(df['close'], window=self.config.EMA_SLOW).ema_indicator()
            
            rsi = RSIIndicator(df['close'], window=self.config.RSI_PERIOD).rsi()
            
            atr = AverageTrueRange(df['high'], df['low'], df['close'], 
                                   window=self.config.ATR_PERIOD).average_true_range()
            
            volume_sma = df['volume'].rolling(window=self.config.VOLUME_SMA).mean()
            
            indicators = {
                'ema9': ema9.iloc[-1],
                'ema21': ema21.iloc[-1],
                'ema50': ema50.iloc[-1],
                'rsi': rsi.iloc[-1],
                'atr': atr.iloc[-1],
                'volume_sma': volume_sma.iloc[-1],
                'current_volume': df['volume'].iloc[-1]
            }
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return {}
    
    def _detect_patterns(self, df: pd.DataFrame) -> List[str]:
        patterns = []
        
        try:
            if len(df) < 3:
                return patterns
            
            c1 = df.iloc[-3]  
            c2 = df.iloc[-2]  
            c3 = df.iloc[-1]  
            
            if self._is_hammer(c3):
                patterns.append('Hammer')
            
            if self._is_bullish_engulfing(c2, c3):
                patterns.append('Bullish Engulfing')
            
            if self._is_morning_star(c1, c2, c3):
                patterns.append('Morning Star')
            
            if self._is_shooting_star(c3):
                patterns.append('Shooting Star')
            
            if self._is_bearish_engulfing(c2, c3):
                patterns.append('Bearish Engulfing')
            
            if self._is_evening_star(c1, c2, c3):
                patterns.append('Evening Star')
            
        except Exception as e:
            logger.error(f"Error detecting patterns: {e}")
        
        return patterns
    
    def _is_hammer(self, candle) -> bool:
        body = abs(candle['close'] - candle['open'])
        lower_shadow = min(candle['open'], candle['close']) - candle['low']
        upper_shadow = candle['high'] - max(candle['open'], candle['close'])
        
        return (lower_shadow > body * 2 and 
                upper_shadow < body * 0.3 and 
                candle['close'] > candle['open'])
    
    def _is_shooting_star(self, candle) -> bool:
        body = abs(candle['close'] - candle['open'])
        upper_shadow = candle['high'] - max(candle['open'], candle['close'])
        lower_shadow = min(candle['open'], candle['close']) - candle['low']
        
        return (upper_shadow > body * 2 and 
                lower_shadow < body * 0.3 and 
                candle['close'] < candle['open'])
    
    def _is_bullish_engulfing(self, c1, c2) -> bool:
        return (c1['close'] < c1['open'] and  
                c2['close'] > c2['open'] and  
                c2['open'] < c1['close'] and  
                c2['close'] > c1['open'])     
    
    def _is_bearish_engulfing(self, c1, c2) -> bool:
        return (c1['close'] > c1['open'] and  
                c2['close'] < c2['open'] and  
                c2['open'] > c1['close'] and  
                c2['close'] < c1['open'])     
    
    def _is_morning_star(self, c1, c2, c3) -> bool:
        body1 = abs(c1['close'] - c1['open'])
        body2 = abs(c2['close'] - c2['open'])
        body3 = abs(c3['close'] - c3['open'])
        
        return (c1['close'] < c1['open'] and      
                body2 < body1 * 0.3 and           
                c3['close'] > c3['open'] and      
                c3['close'] > (c1['open'] + c1['close']) / 2) 
    
    def _is_evening_star(self, c1, c2, c3) -> bool:
        body1 = abs(c1['close'] - c1['open'])
        body2 = abs(c2['close'] - c2['open'])
        body3 = abs(c3['close'] - c3['open'])
        
        return (c1['close'] > c1['open'] and      
                body2 < body1 * 0.3 and           
                c3['close'] < c3['open'] and      
                c3['close'] < (c1['open'] + c1['close']) / 2)
    
    def _find_sr_levels(self, orderbook: Optional[Dict], current_price: float) -> Dict:
        sr_levels = {'support': [], 'resistance': []}
        
        if not orderbook:
            return sr_levels
        
        try:
            threshold_pct = self.config.SR_DISTANCE_PERCENT / 100
            price_range = current_price * threshold_pct
            
            bids = orderbook.get('bids', [])
            bid_volumes = {}
            
            for price, volume in bids:
                if abs(price - current_price) <= price_range:
                    price_level = round(price, 2)
                    bid_volumes[price_level] = bid_volumes.get(price_level, 0) + volume
            
            asks = orderbook.get('asks', [])
            ask_volumes = {}
            
            for price, volume in asks:
                if abs(price - current_price) <= price_range:
                    price_level = round(price, 2)
                    ask_volumes[price_level] = ask_volumes.get(price_level, 0) + volume
            
            if bid_volumes:
                sorted_bids = sorted(bid_volumes.items(), key=lambda x: x[1], reverse=True)[:3]
                sr_levels['support'] = [{'price': p, 'volume': v} for p, v in sorted_bids]
            
            if ask_volumes:
                sorted_asks = sorted(ask_volumes.items(), key=lambda x: x[1], reverse=True)[:3]
                sr_levels['resistance'] = [{'price': p, 'volume': v} for p, v in sorted_asks]
            
        except Exception as e:
            logger.error(f"Error finding S/R levels: {e}")
        
        return sr_levels
    
    def check_rsi_divergence(self, df: pd.DataFrame, rsi_series: pd.Series) -> Optional[str]:
        try:
            if len(df) < 20:
                return None
            
            prices = df['close'].iloc[-20:].values
            rsi = rsi_series.iloc[-20:].values
            
            if (prices[-1] < prices[-10] < prices[-20] and 
                rsi[-1] > rsi[-10] > rsi[-20]):
                return 'bullish'
            
            if (prices[-1] > prices[-10] > prices[-20] and 
                rsi[-1] < rsi[-10] < rsi[-20]):
                return 'bearish'
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking divergence: {e}")
            return None
