import asyncio
import logging
from telegram.ext import Application, CommandHandler

from config import Config
from analysis.fetcher import DataFetcher
from analysis.technical import TechnicalAnalyzer
from analysis.signals import SignalGenerator
from bot.handlers import BotHandlers
from bot.scheduler import ScanScheduler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('scanner.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class Scanner:
    def __init__(self, config):
        self.config = config
        self.fetcher = DataFetcher(config)
        self.analyzer = TechnicalAnalyzer(config)
        self.signal_generator = SignalGenerator(config)
    
    async def scan(self):
        try:
            pairs = await self.fetcher.get_liquid_pairs()
            logger.info(f"Scanning {len(pairs)} pairs")
            
            signals = []
            for symbol in pairs:
                try:
                    data = await self.fetcher.fetch_symbol_data(symbol)
                    if not data:
                        continue
                    
                    analysis = self.analyzer.analyze(data)
                    if not analysis:
                        continue
                    
                    signal = self.signal_generator.generate_signal(analysis)
                    if signal:
                        signals.append(signal)
                        
                except Exception as e:
                    logger.error(f"Error processing {symbol}: {e}")
                    continue
            
            return signals
            
        except Exception as e:
            logger.error(f"Error in scan: {e}")
            return []

async def main():
    logger.info("=" * 50)
    logger.info("Starting BingX Futures Scanner Bot")
    logger.info("=" * 50)
    
    config = Config()
    logger.info(f"Configuration loaded: {config.SCAN_INTERVAL_SECONDS}s interval")
    
    scanner = Scanner(config)
    
    logger.info("Initializing Telegram bot...")
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    
    handlers = BotHandlers(config, scanner)
    
    application.add_handler(CommandHandler("start", handlers.start_command))
    application.add_handler(CommandHandler("scan_now", handlers.scan_now_command))
    application.add_handler(CommandHandler("stats", handlers.stats_command))
    application.add_handler(CommandHandler("settings", handlers.settings_command))
    application.add_handler(CommandHandler("pairs", handlers.pairs_command))
    application.add_handler(CommandHandler("pause", handlers.pause_command))
    application.add_handler(CommandHandler("resume", handlers.resume_command))
    application.add_handler(CommandHandler("test", handlers.test_command))
    application.add_handler(CommandHandler("set_score", handlers.set_score_command))
    application.add_handler(CommandHandler("toggle_long", handlers.toggle_long_command))
    application.add_handler(CommandHandler("toggle_short", handlers.toggle_short_command))
    application.add_handler(CommandHandler("strong_only", handlers.strong_only_command))
    application.add_handler(CommandHandler("reset", handlers.reset_command))
    
    logger.info("Commands registered")
    
    scheduler = ScanScheduler(application.bot, scanner, handlers, config)
    
    try:
        await application.bot.send_message(
            chat_id=config.TELEGRAM_CHAT_ID,
            text="🚀 <b>BingX Scanner Bot запущен!</b>\n\n"
                 f"Интервал сканирования: {config.SCAN_INTERVAL_SECONDS}с\n"
                 f"Минимальный балл сигнала: {config.MIN_SIGNAL_SCORE}\n\n"
                 "Используйте /help для списка команд.",
            parse_mode='HTML'
        )
        logger.info("Startup message sent")
    except Exception as e:
        logger.error(f"Failed to send startup message: {e}")
    
    logger.info("Starting bot and scheduler...")
    
    await asyncio.gather(
        application.run_polling(),
        scheduler.start()
    )

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
