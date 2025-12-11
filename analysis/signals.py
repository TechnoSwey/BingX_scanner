from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)

class SignalGenerator:
    def __init__(self, config):
        self.config = config
    
    def generate_signal(self, analysis: Dict) -> Optional[Dict]:
        try:
            if not analysis:
                return None
            
            long_signal = self._evaluate_long(analysis)
            short_signal = self._evaluate_short(analysis)
            
            if long_signal and long_signal['score'] >= self.config.MIN_SIGNAL_SCORE:
                if short_signal and short_signal['score'] > long_signal['score']:
                    return short_signal
                return long_signal
            
            if short_signal and short_signal['score'] >= self.config.MIN_SIGNAL_SCORE:
                return short_signal
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating signal: {e}")
            return None
    
    def _evaluate_long(self, analysis: Dict) -> Optional[Dict]:
        score = 0
        details = []
        
        ind_5m = analysis['indicators_5m']
        ind_1m = analysis['indicators_1m']
        patterns = analysis['patterns']
        sr_levels = analysis['sr_levels']
        price = analysis['price']
        
        
        if ind_5m['ema9'] > ind_5m['ema21']:
            score += 1
            details.append("✓ EMA9 > EMA21")
        
        if price > ind_5m['ema21']:
            score += 1
            details.append("✓ Price > EMA21")
        
        if self.config.RSI_LONG_MIN <= ind_5m['rsi'] <= self.config.RSI_LONG_MAX:
            score += 1
            details.append(f"✓ RSI in LONG zone ({ind_5m['rsi']:.1f})")
        
        if ind_5m['current_volume'] > ind_5m['volume_sma']:
            score += 1
            volume_ratio = ind_5m['current_volume'] / ind_5m['volume_sma']
            details.append(f"✓ Volume above average ({volume_ratio:.2f}x)")
            
            if volume_ratio >= 2.0:
                score += 1
                details.append(f"✓✓ Strong volume ({volume_ratio:.2f}x)")
        
        bullish_patterns = ['Hammer', 'Bullish Engulfing', 'Morning Star']
        found_patterns = [p for p in patterns if p in bullish_patterns]
        if found_patterns:
            score += 1
            details.append(f"✓ Pattern: {', '.join(found_patterns)}")
        
        if ind_1m['rsi'] > 50:
            score += 1
            details.append(f"✓ M1 confirmation (RSI: {ind_1m['rsi']:.1f})")
        
        near_support = self._check_near_level(price, sr_levels['support'], ind_5m['atr'])
        if near_support:
            score += 1
            details.append(f"✓ Near support: ${near_support['price']:.2f}")
        
        
        if (ind_5m['ema9'] > ind_5m['ema21'] > ind_5m['ema50']):
            score += 2
            details.append("✓✓ Perfect EMA alignment")
        
        if score < self.config.MIN_SIGNAL_SCORE:
            return None
        
        strength = "СИЛЬНЫЙ" if score >= 7 else "СРЕДНИЙ"
        
        return {
            'symbol': analysis['symbol'],
            'direction': 'LONG',
            'strength': strength,
            'score': score,
            'max_score': 10,
            'price': price,
            'details': details,
            'indicators_5m': ind_5m,
            'indicators_1m': ind_1m,
            'patterns': found_patterns,
            'sr_level': near_support,
            'timestamp': analysis['timestamp']
        }
    
    def _evaluate_short(self, analysis: Dict) -> Optional[Dict]:
        score = 0
        details = []
        
        ind_5m = analysis['indicators_5m']
        ind_1m = analysis['indicators_1m']
        patterns = analysis['patterns']
        sr_levels = analysis['sr_levels']
        price = analysis['price']
        
        
        if ind_5m['ema9'] < ind_5m['ema21']:
            score += 1
            details.append("✓ EMA9 < EMA21")
        
        if price < ind_5m['ema21']:
            score += 1
            details.append("✓ Price < EMA21")
        
        if self.config.RSI_SHORT_MIN <= ind_5m['rsi'] <= self.config.RSI_SHORT_MAX:
            score += 1
            details.append(f"✓ RSI in SHORT zone ({ind_5m['rsi']:.1f})")
        
        if ind_5m['current_volume'] > ind_5m['volume_sma']:
            score += 1
            volume_ratio = ind_5m['current_volume'] / ind_5m['volume_sma']
            details.append(f"✓ Volume above average ({volume_ratio:.2f}x)")
            
            if volume_ratio >= 2.0:
                score += 1
                details.append(f"✓✓ Strong volume ({volume_ratio:.2f}x)")
        
        bearish_patterns = ['Shooting Star', 'Bearish Engulfing', 'Evening Star']
        found_patterns = [p for p in patterns if p in bearish_patterns]
        if found_patterns:
            score += 1
            details.append(f"✓ Pattern: {', '.join(found_patterns)}")
        
        if ind_1m['rsi'] < 50:
            score += 1
            details.append(f"✓ M1 confirmation (RSI: {ind_1m['rsi']:.1f})")
        
        near_resistance = self._check_near_level(price, sr_levels['resistance'], ind_5m['atr'])
        if near_resistance:
            score += 1
            details.append(f"✓ Near resistance: ${near_resistance['price']:.2f}")
        
        
        if (ind_5m['ema9'] < ind_5m['ema21'] < ind_5m['ema50']):
            score += 2
            details.append("✓✓ Perfect EMA alignment")
        
        if score < self.config.MIN_SIGNAL_SCORE:
            return None
        
        strength = "СИЛЬНЫЙ" if score >= 7 else "СРЕДНИЙ"
        
        return {
            'symbol': analysis['symbol'],
            'direction': 'SHORT',
            'strength': strength,
            'score': score,
            'max_score': 10,
            'price': price,
            'details': details,
            'indicators_5m': ind_5m,
            'indicators_1m': ind_1m,
            'patterns': found_patterns,
            'sr_level': near_resistance,
            'timestamp': analysis['timestamp']
        }
    
    def check_near_level(self, price: float, levels: List[Dict], atr: float) -> Optional[Dict]:
        if not levels:
            return None
        
        threshold = atr * (self.config.SR_CLOSE_PERCENT / 100)
        
        for level in levels:
            level_price = level['price']
            if abs(price - level_price) <= threshold:
                return level
        
        return None
