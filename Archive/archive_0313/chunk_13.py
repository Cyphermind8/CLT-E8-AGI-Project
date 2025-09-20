# Chunk 13: AI-Based Image Recognition (Basic CNN)

import numpy as np

class BasicImageClassifier:
    """A simple AI-powered image classifier using a dummy model."""
    def __init__(self):
        self.labels = ["Cat", "Dog", "Car", "Tree"]

    def classify(self, image_data):
        """Classify an image into a category."""
        return np.random.choice(self.labels)

def image_recognition_example():
    """Example usage of a simple AI image classifier."""
    dummy_image_data = np.random.rand(64, 64)  # Simulating an image
    classifier = BasicImageClassifier()
    prediction = classifier.classify(dummy_image_data)

    print(f"AI Image Recognition Result: {prediction}")

# Example usage
image_recognition_example()
