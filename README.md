# Telegram Text Formatter Bot

Bot that receives raw exchange transaction text and reformats it into a clean, beautiful format.

## Quick Start (local)

```bash
cp .env.example .env
# edit .env and paste your BOT_TOKEN
pip install -r requirements.txt
python bot.py
```

## Deploy to Server (SSH Deploy Key)

One command does everything:

```bash
# on your server (Ubuntu/Debian)
bash <(curl -s https://raw.githubusercontent.com/armcoincrypto/changetext/claude/telegram-text-formatter-bot-qesQW/deploy/setup.sh)
```

Or step by step:

```bash
# 1. Clone this repo to your server
git clone git@github.com:armcoincrypto/changetext.git /opt/changetext
cd /opt/changetext

# 2. Run the setup script
bash deploy/setup.sh
```

The setup script will:
- Generate an SSH deploy key (add it to GitHub when prompted)
- Clone / update the repo to `/opt/changetext`
- Ask for your `BOT_TOKEN` and create `.env`
- Install Python dependencies
- Create and start a systemd service

## Update

```bash
bash /opt/changetext/deploy/update.sh
```

## Manage

| Command | Description |
|---|---|
| `systemctl status changetext-bot` | Check status |
| `systemctl restart changetext-bot` | Restart |
| `systemctl stop changetext-bot` | Stop |
| `journalctl -u changetext-bot -f` | Live logs |

## Usage

1. Send `/start` to the bot
2. Paste your raw transaction text
3. Enter card number (or `-` to skip)
4. Enter Telegram username (or `-` to skip)
5. Select account type (СБП, Карта, Счёт)
6. Get the formatted result

## Project Structure

```
changetext/
├── bot.py                          # Main bot code
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment template
├── .gitignore
├── deploy/
│   ├── changetext-bot.service      # systemd unit file
│   ├── setup.sh                    # Full deploy script
│   └── update.sh                   # Quick update script
└── README.md
```
