from typing import Dict, List
from datetime import datetime

def format_signal_message(signal: Dict) -> str:
    direction_emoji = "🟢" if signal['direction'] == 'LONG' else "🔴"
    strength_emoji = "⚡" if signal['strength'] == 'СИЛЬНЫЙ' else "📊"
    
    message = f"{direction_emoji} <b>{signal['direction']} SIGNAL</b> {strength_emoji}\n"
    message += f"<b>Пара:</b> {signal['symbol']}\n"
    message += f"<b>Сила:</b> {signal['strength']} ({signal['score']}/{signal['max_score']})\n"
    message += f"<b>Цена:</b> ${signal['price']:.4f}\n"
    message += "━━━━━━━━━━━━━━━━━━\n\n"
    
    ind_5m = signal['indicators_5m']
    message += "📊 <b>Индикаторы M5:</b>\n"
    message += f"• EMA9: ${ind_5m['ema9']:.2f}\n"
    message += f"• EMA21: ${ind_5m['ema21']:.2f}\n"
    message += f"• EMA50: ${ind_5m['ema50']:.2f}\n"
    message += f"• RSI: {ind_5m['rsi']:.1f}\n"
    message += f"• ATR: ${ind_5m['atr']:.2f}\n"
    
    volume_ratio = ind_5m['current_volume'] / ind_5m['volume_sma']
    message += f"• Volume: {_format_volume(ind_5m['current_volume'])} "
    message += f"({volume_ratio:.2f}x avg)\n\n"
    
    ind_1m = signal['indicators_1m']
    message += "⚡ <b>Подтверждение M1:</b>\n"
    message += f"• RSI: {ind_1m['rsi']:.1f}\n\n"
    
    if signal['patterns']:
        message += f"🕯 <b>Паттерны:</b> {', '.join(signal['patterns'])}\n\n"
    
    if signal['sr_level']:
        sr = signal['sr_level']
        level_type = "Support" if signal['direction'] == 'LONG' else "Resistance"
        message += f"📍 <b>{level_type}:</b> ${sr['price']:.2f} "
        message += f"(vol: {_format_volume(sr['volume'])})\n\n"
    
    message += "<b>🎯 Детали сигнала:</b>\n"
    for detail in signal['details']:
        message += f"{detail}\n"
    
    message += "\n━━━━━━━━━━━━━━━━━━\n"
    
    message += _generate_trade_recommendations(signal)
    
    timestamp = signal['timestamp'].strftime('%H:%M:%S')
    message += f"\n\n<i>⏰ {timestamp}</i>"
    
    return message

def _format_volume(volume: float) -> str:
    if volume >= 1_000_000_000:
        return f"${volume/1_000_000_000:.2f}B"
    elif volume >= 1_000_000:
        return f"${volume/1_000_000:.2f}M"
    elif volume >= 1_000:
        return f"${volume/1_000:.2f}K"
    else:
        return f"${volume:.2f}"

def _generate_trade_recommendations(signal: Dict) -> str:
    price = signal['price']
    atr = signal['indicators_5m']['atr']
    direction = signal['direction']
    
    if direction == 'LONG':
        entry = price
        stop_loss = price - (atr * 1.5)
        take_profit_1 = price + (atr * 2)
        take_profit_2 = price + (atr * 3)
        take_profit_3 = price + (atr * 4)
    else:
        entry = price
        stop_loss = price + (atr * 1.5)
        take_profit_1 = price - (atr * 2)
        take_profit_2 = price - (atr * 3)
        take_profit_3 = price - (atr * 4)
    
    risk = abs(entry - stop_loss)
    reward_1 = abs(take_profit_1 - entry)
    rr_ratio = reward_1 / risk
    
    rec = "<b>💡 Рекомендации для входа:</b>\n"
    rec += f"• Entry: ${entry:.4f}\n"
    rec += f"• Stop Loss: ${stop_loss:.4f}\n"
    rec += f"• Take Profit 1: ${take_profit_1:.4f} (50%)\n"
    rec += f"• Take Profit 2: ${take_profit_2:.4f} (30%)\n"
    rec += f"• Take Profit 3: ${take_profit_3:.4f} (20%)\n"
    rec += f"• Risk/Reward: 1:{rr_ratio:.2f}\n"
    
    return rec

def format_scan_summary(signals: list, scan_time: float) -> str:
    message = "🔍 <b>Сканирование завершено</b>\n\n"
    message += f"⏱ Время: {scan_time:.2f}с\n"
    message += f"📊 Найдено сигналов: {len(signals)}\n"
    
    if signals:
        long_count = sum(1 for s in signals if s['direction'] == 'LONG')
        short_count = sum(1 for s in signals if s['direction'] == 'SHORT')
        strong_count = sum(1 for s in signals if s['strength'] == 'СИЛЬНЫЙ')
        
        message += f"🟢 LONG: {long_count}\n"
        message += f"🔴 SHORT: {short_count}\n"
        message += f"⚡ Сильных: {strong_count}\n"
    
    return message

def format_error_message(error: Exception) -> str:
    message = "❌ <b>Ошибка</b>\n\n"
    message += f"<code>{str(error)}</code>\n"
    return message
