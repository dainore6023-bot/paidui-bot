import os
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    filters
)

TOKEN = os.getenv("BOT_TOKEN")

DATA_FILE = "queue.json"

queue = []


def load_queue():
    global queue
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            queue = json.load(f)
    except:
        queue = []


def save_queue():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(queue, f, ensure_ascii=False)


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

    def log_message(self, format, *args):
        return


def run_web():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()


async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    text = update.message.text
    user = update.message.from_user
    name = user.full_name

    if text == "排队":

        if any(x["id"] == user.id for x in queue):
            await update.message.reply_text("你已经在排队中了。")
            return

        queue.append({
            "id": user.id,
            "name": name
        })

        save_queue()
        await show_queue(update)


    elif text == "取消":

        queue[:] = [
            x for x in queue
            if x["id"] != user.id
        ]

        save_queue()

        await update.message.reply_text(
            f"✅ {name} 已取消排队"
        )


    elif text == "查看":

        await show_queue(update)


    elif text == "清空":

        member = await context.bot.get_chat_member(
            update.effective_chat.id,
            user.id
        )

        if member.status in ["administrator", "creator"]:
            queue.clear()
            save_queue()

            await update.message.reply_text(
                "✅ 排队列表已清空"
            )


async def show_queue(update):

    if not queue:
        await update.message.reply_text(
            "📋 当前没有排队人员"
        )
        return

    text = "📋 当前排队：\n\n"

    for i, u in enumerate(queue, 1):
        text += f"{i}. {u['name']}\n"

    await update.message.reply_text(text)



def main():

    load_queue()

    threading.Thread(
        target=run_web,
        daemon=True
    ).start()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            message
        )
    )

    app.run_polling()


if __name__ == "__main__":
    main()
