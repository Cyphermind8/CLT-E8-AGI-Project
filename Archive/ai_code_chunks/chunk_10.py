# Chunk 10: AI-Based Sentiment Analysis

import re
import numpy as np

class SentimentAnalyzer:
    """A basic AI-powered sentiment analysis tool using keyword matching."""
    def __init__(self):
        self.positive_words = {"happy", "great", "excellent", "good", "awesome"}
        self.negative_words = {"bad", "terrible", "awful", "worst", "sad"}

    def clean_text(self, text):
        """Preprocess text by removing non-alphabetic characters."""
        return re.sub(r'[^a-zA-Z\s]', '', text.lower()).split()

    def analyze_sentiment(self, text):
        """Analyze the sentiment of a given text."""
        words = self.clean_text(text)
        pos_count = sum(1 for word in words if word in self.positive_words)
        neg_count = sum(1 for word in words if word in self.negative_words)
        if pos_count > neg_count:
            return "Positive"
        elif neg_count > pos_count:
            return "Negative"
        else:
            return "Neutral"

def sentiment_example():
    """Example usage of sentiment analysis."""
    analyzer = SentimentAnalyzer()
    text = "This movie is absolutely awesome and fantastic!"
    sentiment = analyzer.analyze_sentiment(text)
    print(f"Sentiment: {sentiment}")

# Example usage
sentiment_example()
