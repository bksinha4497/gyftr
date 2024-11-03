import re
import time
import json
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Set up options for headless browsing
chrome_options = Options()
chrome_options.add_argument("--headless")  # Runs Chrome in headless mode
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

# Telegram Bot Token
TELEGRAM_TOKEN = '8008607329:AAEjWQsF3OUKLQAOvQIepCeSc7pCZgaYy-Y'
CHAT_ID = '616796788'


def check_for_vouchers():
    url = "https://www.gyftr.com/amexrewardmultiplier/amazon-gift-vouchers"
    driver.get(url)
    time.sleep(5)  # Allow the page to load

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    script_tags = soup.find_all('script')
    vouchers = {}

    for script in script_tags:
        if "products" in script.text:
            try:
                json_matches = re.findall(r'({.*?})', script.string, re.DOTALL)
                for json_text in json_matches:
                    try:
                        json_data = json.loads(json_text)
                        print(f"json_data- {json_data}")
                        if isinstance(json_data, dict) and 'available_qty' in json_data:
                            name = json_data.get("name")
                            price = json_data.get("price")
                            available_qty = json_data.get("available_qty")
                            # If the name is not in the dictionary, add it
                            if name not in vouchers:
                                vouchers[name] = []
                            # Create a new dictionary for the current voucher
                            voucher_detail = {
                                "Price": price,
                                "Available Quantity": available_qty
                            }

                            # Check if this voucher detail already exists in the list to prevent duplicates
                            if voucher_detail not in vouchers[name]:
                                vouchers[name].append(voucher_detail)

                    except json.JSONDecodeError:
                        pass
            except Exception as e:
                logging.error(f"An error occurred: {e}")

    return vouchers


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Bot started! I will send you voucher updates automatically.')


async def send_vouchers(context):
    vouchers = check_for_vouchers()
    print(f"vouchers - {vouchers}")

    if vouchers:
        message = "Vouchers Found:\n\n"
        for name, details in vouchers.items():
            message += f"{name}:\n"
            for detail in details:
                message += f"  - Price: ₹{detail['Price']}, Available Quantity: {detail['Available Quantity']}\n"
            message += "\n"  # Add a newline for better separation between vouchers

        # Send the formatted message
        await context.bot.send_message(chat_id=CHAT_ID, text=message)

        # Sleep for 15 days (15 * 24 * 60 * 60 seconds)
        time.sleep(15 * 24 * 60 * 60)

    # If no vouchers are found, continue scraping
    else:
        logging.info("No vouchers found, continuing to scrape...")


def main():
    # Create the Application and pass it your bot's token.
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))

    # Set up the JobQueue to scrape every 10 minutes
    application.job_queue.run_repeating(send_vouchers, interval=600, first=0)  # 600 seconds = 10 minutes

    # Start the Bot
    application.run_polling()


if __name__ == "__main__":
    main()
