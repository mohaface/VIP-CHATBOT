from pyrogram import filters
from pyrogram.enums import ChatAction
from MukeshAPI import api  # Assuming this is your API wrapper
from nexichat import nexichat  # Your bot instance
from deep_translator import GoogleTranslator
from pymongo import MongoClient
from config import MONGO_URL
from typing import Optional
import asyncio
import html

class ChatGPTBot:
    def __init__(self):
        # Initialize MongoDB connection
        self.client = MongoClient(MONGO_URL)
        self.db = self.client['chatbot_db']
        self.conversations = self.db['conversations']
        
        # Initialize translator
        self.translator = GoogleTranslator(source='auto', target='en')

    async def save_conversation(self, user_id: int, message: str, response: str):
        """Save conversation history to MongoDB"""
        try:
            self.conversations.insert_one({
                'user_id': user_id,
                'message': message,
                'response': response,
                'timestamp': datetime.now()
            })
        except Exception as e:
            print(f"Error saving conversation: {e}")

    async def format_response(self, response: str) -> str:
        """Format the bot's response with proper markdown"""
        # Escape special characters
        response = html.escape(response)
        
        # Format code blocks
        if '```' in response:
            response = response.replace('```', '<code>')
            response = response.replace('```', '</code>')
            
        return response

    async def get_response(self, user_input: str) -> Optional[str]:
        """Get response from ChatGPT API with error handling"""
        try:
            response = api.chatgpt(user_input)
            return response if response else None
        except Exception as e:
            print(f"API Error: {e}")
            return None

    @nexichat.on_message(filters.command(["chatgpt", "ai", "ask"]))
    async def chatgpt_chat(self, bot, message):
        """Handle ChatGPT command messages"""
        # Check for valid input
        if len(message.command) < 2 and not message.reply_to_message:
            await message.reply_text(
                "**Usage Examples:**\n\n"
                "1. `/ask write simple website code using html css, js?`\n"
                "2. Reply to any message with `/ask`\n"
                "3. `/chatgpt explain quantum computing`\n"
                "4. `/ai help me debug this code`",
                parse_mode="markdown"
            )
            return

        # Get user input
        if message.reply_to_message and message.reply_to_message.text:
            user_input = message.reply_to_message.text
        else:
            user_input = " ".join(message.command[1:])

        # Show typing indicator
        await bot.send_chat_action(message.chat.id, ChatAction.TYPING)

        try:
            # Translate input if not in English
            try:
                detected_lang = self.translator.detect(user_input)
                if detected_lang != 'en':
                    user_input = self.translator.translate(user_input)
            except:
                pass  # Continue with original input if translation fails

            # Get response from ChatGPT
            response = await self.get_response(user_input)
            
            if response:
                # Format response
                formatted_response = await self.format_response(response)
                
                # Save conversation
                await self.save_conversation(
                    message.from_user.id,
                    user_input,
                    response
                )
                
                # Send response
                await message.reply_text(
                    formatted_response,
                    parse_mode="html",
                    disable_web_page_preview=True
                )
            else:
                await message.reply_text(
                    "😕 I couldn't generate a good response. Please try rephrasing your question."
                )

        except Exception as e:
            print(f"Error in chatgpt_chat: {e}")
            await message.reply_text(
                "❌ An error occurred while processing your request.\n"
                "Please try again later or contact support if the issue persists."
            )

    async def handle_rate_limit(self):
        """Handle API rate limiting"""
        await asyncio.sleep(1)  # Add delay between requests

# Initialize the bot
chatgpt_bot = ChatGPTBot()
