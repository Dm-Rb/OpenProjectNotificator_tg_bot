# OpenProject Telegram Notifications Bot

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.68+-green.svg)](https://fastapi.tiangolo.com)
[![aiogram](https://img.shields.io/badge/aiogram-3.0+-blue.svg)](https://docs.aiogram.dev/)

A Telegram bot for receiving notifications about project and task updates in OpenProject. The bot accepts webhooks from OpenProject and sends brief informational notifications to users associated with the project or task.
<img width="711" height="493" alt="изображение" src="https://github.com/user-attachments/assets/96c1c5d6-fc68-4261-8d5b-125fed92c00e" />


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
```
## Configuration Setup

- Create a .env file in the project root:
```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
SERVER_HOST=localhost
SERVER_PORT=8484
OPENPROJECT_DOMAIN=https://your-openproject-instance.com
OPENPROJECT_USER_API_KEY=user-token
DIR_PATH=./data
```
Note:
 DIR_PATH - file system path for storing log files and SQLite database with users
 OPENPROJECT_USER_API_KEY - more details in the "User API Token Creation" paragraph.

## Webhook Configuration in OpenProject

1. Navigate to: Administrator → "Webhooks"

2. Add a new webhook with URL: https://your-fast-api-server:port/webhook

3. Select events to track (project and task updates)

## Webhook Testing

Run the get_webhook_test.py module in the project root. With successful configuration, you'll see webhook content in JSON format in the terminal when a task is updated.

## User API Token Creation

1. Register an account in OpenProject with administrator rights. This account will serve as a service account. The access token will be used for making requests to the OpenProject API to obtain more detailed information not contained in the webhook body.

2. Log in with this account

3. Navigate to: "My Account" → "Access tokens"

4. Create a new token with administrator rights

5. Specify the token in the .env file in the OPENPROJECT_USER_API_KEY variable

## Bot Launch
```
python3 run.py
```

🔧 Usage

Getting Started: User starts the bot with the /start command

Registration: Bot requests OpenProject login and saves the OpenProject login → Telegram ID mapping

Notifications: When updates occur in OpenProject, the bot automatically sends notifications:

- Brief description of the change

- Link to the task/project


