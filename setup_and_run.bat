@echo off
cd /d "%~dp0"
echo Создание виртуального окружения...
python -m venv venv
call venv\Scripts\activate
echo Установка зависимостей...
pip install --upgrade pip
pip install -r requirements.txt
echo Запуск Telegram-бота...
python bot.py
pause
