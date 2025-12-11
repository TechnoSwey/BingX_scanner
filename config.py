import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    SCAN_INTERVAL_SECONDS = int(os.getenv('SCAN_INTERVAL_SECONDS', 120))
    MIN_VOLUME_USDT = float(os.getenv('MIN_VOLUME_USDT', 50000000))
    MIN_SIGNAL_SCORE = int(os.getenv('MIN_SIGNAL_SCORE', 5))
    
    MAX_REQUESTS_PER_SECOND = int(os.getenv('MAX_REQUESTS_PER_SECOND', 10))
    MAX_CONCURRENT_REQUESTS = int(os.getenv('MAX_CONCURRENT_REQUESTS', 5))
    
    EMA_FAST = 9
    EMA_MEDIUM = 21
    EMA_SLOW = 50
    RSI_PERIOD = 14
    ATR_PERIOD = 14
    VOLUME_SMA = 20
    
    RSI_LONG_MIN = 50
    RSI_LONG_MAX = 65
    RSI_SHORT_MIN = 35
    RSI_SHORT_MAX = 50
    RSI_OVERSOLD = 30
    RSI_OVERBOUGHT = 70
    
    SR_DISTANCE_PERCENT = 2.0
    SR_CLOSE_PERCENT = 0.5
    
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = 'bot.log'
    
    PAIRS_CACHE_HOURS = 1
