# Chunk 15: AI-Powered Chatbot

import random

class SimpleChatbot:
    """A basic AI-powered chatbot that provides predefined responses."""
    def __init__(self):
        self.responses = {
            "hello": "Hi there! How can I assist you?",
            "how are you": "I'm just an AI, but I'm here to help!",
            "bye": "Goodbye! Have a great day!",
            "default": "I'm not sure how to respond to that."
        }

    def respond(self, message):
        """Return a response based on the input message."""
        return self.responses.get(message.lower(), self.responses["default"])

def chatbot_example():
    """Example usage of an AI-powered chatbot."""
    chatbot = SimpleChatbot()
    user_input = "hello"
    response = chatbot.respond(user_input)

    print(f"User: {user_input}")
    print(f"AI Chatbot: {response}")

# Example usage
chatbot_example()
