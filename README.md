OpenProject Telegram Notifications Bot

https://img.shields.io/badge/Python-3.8+-blue.svg
https://img.shields.io/badge/FastAPI-0.68+-green.svg
https://img.shields.io/badge/aiogram-3.0+-blue.svg

A Telegram bot for receiving notifications about project and task updates in OpenProject. The bot accepts webhooks from OpenProject and sends brief informational notifications to users associated with the project or task.
🚀 Key Features

    📨 Webhook Reception from OpenProject via FastAPI web server

    👥 Smart Notification Distribution only to relevant participants (the user who initiated the update does not receive a notification)

    🔗 Quick Access to tasks through direct links

🏗 Architecture

The project consists of three main components:

    🌐 FastAPI Web Server - receives webhooks from OpenProject

    ⚙️ Webhook Handler - extracts information and forms recipient list

    🤖 Telegram Bot on aiogram - performs notification distribution

📋 Prerequisites

    Python 3.8+

    OpenProject account with administrator rights

    Telegram bot (create via @BotFather)

⚙️ Installation and Configuration
Installing Dependencies
``pip install -r requirements.txt``

Configuration Setup

Create a .env file in the project root:
    ``` TELEGRAM_BOT_TOKEN=your_telegram_bot_token
    SERVER_HOST=localhost
    SERVER_PORT=8484
    OPENPROJECT_DOMAIN=https://your-openproject-instance.com
    OPENPROJECT_USER_API_KEY=your_openproject_api_key
    DIR_PATH=./data
    ```
    Note: DIR_PATH - file system path for storing log files and SQLite database with users

Webhook Configuration in OpenProject

    Navigate to: Administrator → "Webhooks"

    Add a new webhook with URL: https://your-server:8484/webhook

    Select events to track (project and task updates)

Webhook Testing

Run the get_webhook_test.py module in the project root. With successful configuration, you'll see webhook content in JSON format in the terminal when a task is updated.
API Token Creation

    Register an account in OpenProject with administrator rights

    Log in with this account

    Navigate to: "My Account" → "Access tokens"

    Create a new token with administrator rights

    Specify the token in the .env file in the OPENPROJECT_USER_API_KEY variable

    Note: This account will serve as a service account. The access token will be used for making requests to the OpenProject API to obtain more detailed information not contained in the webhook body.
