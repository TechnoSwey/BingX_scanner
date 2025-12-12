import asyncio
from datetime import datetime
import logging

from bot.messages import format_signal_message, format_scan_summary, format_error_message

logger = logging.getLogger(__name__)

class ScanScheduler:
    def __init__(self, bot, scanner, handlers, config):
        self.bot = bot
        self.scanner = scanner
        self.handlers = handlers
        self.config = config
        self.is_running = False
        self.is_paused = False
        self.last_scan_time = None
    
    async def start(self):
        self.is_running = True
        logger.info("Scheduler started")
        
        await self._run_loop()
    
    async def stop(self):
        self.is_running = False
        logger.info("Scheduler stopped")
    
    async def pause(self):
        self.is_paused = True
        logger.info("Scanning paused")
    
    async def resume(self):
        self.is_paused = False
        logger.info("Scanning resumed")
    
    async def _run_loop(self):
        while self.is_running:
            try:
                if not self.is_paused:
                    await self._perform_scan()
                
                await asyncio.sleep(self.config.SCAN_INTERVAL_SECONDS)
                
            except Exception as e:
                logger.error(f"Error in scan loop: {e}")
                await asyncio.sleep(60)
    
    async def _perform_scan(self):
        start_time = datetime.now()
        logger.info("Starting scheduled scan...")
        
        try:
            signals = await self.scanner.scan()
            
            scan_time = (datetime.now() - start_time).total_seconds()
            self.last_scan_time = datetime.now()
            
            self.handlers.increment_stats(scans=1)
            
            if signals:
                await self._send_signals(signals)
                
                summary = format_scan_summary(signals, scan_time)
                await self._send_to_admin(summary)
            else:
                logger.info(f"No signals found. Scan took {scan_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Error during scan: {e}")
            await self._send_to_admin(format_error_message(e))
    
    async def _send_signals(self, signals: list):
        sent_count = 0
        
        for signal in signals:
            try:
                message = format_signal_message(signal)
                
                await self.bot.send_message(
                    chat_id=self.config.TELEGRAM_CHAT_ID,
                    text=message,
                    parse_mode='HTML'
                )
                
                sent_count += 1
                logger.info(f"Signal sent: {signal['symbol']} {signal['direction']}")
                
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error sending signal: {e}")
        
        self.handlers.increment_stats(signals=sent_count)
    
    async def _send_to_admin(self, message: str):
        try:
            await self.bot.send_message(
                chat_id=self.config.TELEGRAM_CHAT_ID,
                text=message,
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Error sending to admin: {e}")
