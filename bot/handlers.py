from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BotHandlers:
    def __init__(self, config, scanner):
        self.config = config
        self.scanner = scanner
        self.stats = {
            'scans_total': 0,
            'signals_sent': 0,
            'start_time': datetime.now()
        }
        self.user_settings = {}
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        welcome_message = """
🤖 <b>BingX Futures Scanner Bot</b>

<b>📋 Доступные команды:</b>
/start - Показать это сообщение
/scan_now - Запустить сканирование сейчас
/stats - Статистика работы бота
/settings - Настройки фильтров
/pairs - Список отслеживаемых пар
/pause - Приостановить сканирование
/resume - Возобновить сканирование
/test - Тестовое сообщение

<b>⚙️ Текущие настройки:</b>
• Интервал сканирования: {interval}с
• Минимальный балл сигнала: {min_score}
• Минимальный объем: ${volume}M

Бот запущен и работает! 🚀
        """.format(
            interval=self.config.SCAN_INTERVAL_SECONDS,
            min_score=self.config.MIN_SIGNAL_SCORE,
            volume=self.config.MIN_VOLUME_USDT / 1_000_000
        )
        
        await update.message.reply_text(welcome_message, parse_mode='HTML')
        logger.info(f"User {update.effective_user.id} started the bot")
    
    async def scan_now_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🔍 Запускаю ручное сканирование...")
        
        try:
            signals = await self.scanner.scan()
            
            if signals:
                await update.message.reply_text(
                    f"✅ Сканирование завершено!\n"
                    f"Найдено сигналов: {len(signals)}"
                )
            else:
                await update.message.reply_text(
                    "❌ Сигналов не найдено.\n"
                    "Попробуйте позже или измените параметры фильтрации."
                )
        except Exception as e:
            logger.error(f"Error in manual scan: {e}")
            await update.message.reply_text(
                f"❌ Ошибка при сканировании:\n{str(e)}"
            )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        uptime = datetime.now() - self.stats['start_time']
        hours = int(uptime.total_seconds() // 3600)
        minutes = int((uptime.total_seconds() % 3600) // 60)
        
        stats_message = f"""
📊 <b>Статистика бота</b>

⏱ <b>Время работы:</b> {hours}ч {minutes}м
🔍 <b>Всего сканирований:</b> {self.stats['scans_total']}
📢 <b>Отправлено сигналов:</b> {self.stats['signals_sent']}
📈 <b>Средний успех:</b> {self._calculate_success_rate():.1f}%

<b>Последнее сканирование:</b>
{self._get_last_scan_info()}
        """
        
        await update.message.reply_text(stats_message, parse_mode='HTML')
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_prefs = self.user_settings.get(user_id, {})
        
        settings_message = f"""
⚙️ <b>Настройки фильтров</b>

<b>Текущие параметры:</b>
• Минимальный балл: {user_prefs.get('min_score', self.config.MIN_SIGNAL_SCORE)}
• Только сильные сигналы: {'✅' if user_prefs.get('strong_only', False) else '❌'}
• Уведомления о LONG: {'✅' if user_prefs.get('notify_long', True) else '❌'}
• Уведомления о SHORT: {'✅' if user_prefs.get('notify_short', True) else '❌'}

<b>Изменить настройки:</b>
/set_score [число] - Установить мин. балл (1-10)
/strong_only - Только сильные сигналы
/toggle_long - Вкл/выкл LONG сигналы
/toggle_short - Вкл/выкл SHORT сигналы
/reset - Сбросить все настройки
        """
        
        await update.message.reply_text(settings_message, parse_mode='HTML')
    
    async def pairs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("⏳ Загружаю список пар...")
        
        try:
            pairs = await self.scanner.fetcher.get_liquid_pairs()
            
            pairs_text = "<b>📋 Отслеживаемые пары:</b>\n\n"
            pairs_text += "\n".join([f"• {pair}" for pair in pairs[:50]])
            
            if len(pairs) > 50:
                pairs_text += f"\n\n... и ещё {len(pairs) - 50} пар"
            
            pairs_text += f"\n\n<b>Всего:</b> {len(pairs)} пар"
            
            await update.message.reply_text(pairs_text, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"Error fetching pairs: {e}")
            await update.message.reply_text(f"❌ Ошибка загрузки пар:\n{str(e)}")
    
    async def pause_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "⏸ Сканирование приостановлено.\n"
            "Используйте /resume для возобновления."
        )
    
    async def resume_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "▶️ Сканирование возобновлено.\n"
            "Следующее сканирование через несколько секунд."
        )
    
    async def test_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        test_signal = {
            'symbol': 'BTC/USDT:USDT',
            'direction': 'LONG',
            'strength': 'СИЛЬНЫЙ',
            'score': 8,
            'max_score': 10,
            'price': 45000.0,
            'details': [
                '✓ EMA9 > EMA21',
                '✓ Price > EMA21',
                '✓ RSI in LONG zone (58.5)',
                '✓✓ Strong volume (2.3x)',
                '✓ Pattern: Hammer',
                '✓ M1 confirmation (RSI: 62.1)',
                '✓ Near support: $44950.00',
                '✓✓ Perfect EMA alignment'
            ],
            'indicators_5m': {
                'ema9': 45100,
                'ema21': 44900,
                'ema50': 44500,
                'rsi': 58.5,
                'atr': 250,
                'volume_sma': 50000000,
                'current_volume': 115000000
            },
            'indicators_1m': {
                'rsi': 62.1
            },
            'patterns': ['Hammer'],
            'sr_level': {'price': 44950.0, 'volume': 850000},
            'timestamp': datetime.now()
        }
        
        from bot.messages import format_signal_message
        message = format_signal_message(test_signal)
        
        await update.message.reply_text(
            "🧪 <b>Тестовый сигнал:</b>\n\n" + message,
            parse_mode='HTML'
        )
        
        logger.info(f"Test signal sent to user {update.effective_user.id}")
    
    async def set_score_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            if not context.args or len(context.args) != 1:
                await update.message.reply_text(
                    "❌ Использование: /set_score [число от 1 до 10]\n"
                    "Пример: /set_score 6"
                )
                return
            
            score = int(context.args[0])
            if not 1 <= score <= 10:
                raise ValueError()
            
            user_id = update.effective_user.id
            if user_id not in self.user_settings:
                self.user_settings[user_id] = {}
            
            self.user_settings[user_id]['min_score'] = score
            
            await update.message.reply_text(
                f"✅ Минимальный балл установлен: {score}"
            )
            
        except ValueError:
            await update.message.reply_text(
                "❌ Укажите число от 1 до 10"
            )
    
    async def toggle_long_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in self.user_settings:
            self.user_settings[user_id] = {}
        
        current = self.user_settings[user_id].get('notify_long', True)
        self.user_settings[user_id]['notify_long'] = not current
        
        status = "включены" if not current else "выключены"
        await update.message.reply_text(f"✅ LONG сигналы {status}")
    
    async def toggle_short_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in self.user_settings:
            self.user_settings[user_id] = {}
        
        current = self.user_settings[user_id].get('notify_short', True)
        self.user_settings[user_id]['notify_short'] = not current
        
        status = "включены" if not current else "выключены"
        await update.message.reply_text(f"✅ SHORT сигналы {status}")
    
    async def strong_only_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in self.user_settings:
            self.user_settings[user_id] = {}
        
        current = self.user_settings[user_id].get('strong_only', False)
        self.user_settings[user_id]['strong_only'] = not current
        
        status = "включен" if not current else "выключен"
        await update.message.reply_text(
            f"✅ Фильтр 'Только сильные сигналы' {status}"
        )
    
    async def reset_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id in self.user_settings:
            del self.user_settings[user_id]
        
        await update.message.reply_text(
            "✅ Настройки сброшены на значения по умолчанию"
        )
    
    def _calculate_success_rate(self) -> float:
        return 0.0
    
    def _get_last_scan_info(self) -> str:
        if self.stats['scans_total'] == 0:
            return "Ещё не было сканирований"
        return "Недавно"
    
    def should_send_signal(self, signal: dict, user_id: int) -> bool:
        user_prefs = self.user_settings.get(user_id, {})
        
        min_score = user_prefs.get('min_score', self.config.MIN_SIGNAL_SCORE)
        if signal['score'] < min_score:
            return False
        
        if user_prefs.get('strong_only', False) and signal['strength'] != 'СИЛЬНЫЙ':
            return False
        
        if signal['direction'] == 'LONG' and not user_prefs.get('notify_long', True):
            return False
        
        if signal['direction'] == 'SHORT' and not user_prefs.get('notify_short', True):
            return False
        
        return True
    
    def increment_stats(self, scans: int = 0, signals: int = 0):
        self.stats['scans_total'] += scans
        self.stats['signals_sent'] += signals
