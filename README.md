# OpenProject Telegram Notifications Bot

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.68+-green.svg)](https://fastapi.tiangolo.com)
[![aiogram](https://img.shields.io/badge/aiogram-3.0+-blue.svg)](https://docs.aiogram.dev/)

A Telegram bot for receiving notifications about project and task updates in OpenProject. The bot accepts webhooks from OpenProject and sends brief informational notifications to users associated with the project or task.

## 🚀 Key Features

- **📨 Webhook Reception** from OpenProject via FastAPI web server
- **👥 Smart Notification Distribution** only to relevant participants (the user who initiated the update does not receive a notification)
- **🔗 Quick Access** to tasks through direct links

## 🏗 Architecture

The project consists of three main components:

1. 🌐 **FastAPI Web Server** - receives webhooks from OpenProject
2. ⚙️ **Webhook Handler** - extracts information and forms recipient list
3. 🤖 **Telegram Bot on aiogram** - performs notification distribution

## 📋 Prerequisites

- Python 3.8+
- OpenProject account with administrator rights
- Telegram bot (create via [@BotFather](https://t.me/BotFather))

## ⚙️ Installation and Configuration

### Installing Dependencies

```bash
pip install -r requirements.txt
