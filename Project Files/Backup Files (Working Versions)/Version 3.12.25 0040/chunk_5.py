# Chunk 5: Convolutional Neural Network (CNN) for image classification

import numpy as np
import random
import math

class ConvolutionalLayer:
    def __init__(self, filter_size, num_filters):
        self.filter_size = filter_size
        self.num_filters = num_filters
        self.filters = np.random.randn(num_filters, filter_size, filter_size) * 0.1  # Small random filters

    def apply_filter(self, image):
        """Apply the filter to the image (2D convolution)."""
        image_size = len(image)
        output_size = image_size - self.filter_size + 1

        if output_size <= 0:
            raise ValueError("Image size too small for convolution operation!")

        filter_output = np.zeros((output_size, output_size))

        for i in range(output_size):
            for j in range(output_size):
                region = image[i:i+self.filter_size, j:j+self.filter_size]
                filter_output[i, j] = np.sum(region * self.filters[0])  # Apply first filter

        return filter_output

class PoolingLayer:
    def __init__(self, pool_size):
        self.pool_size = pool_size

    def apply_pooling(self, feature_map):
        """Apply max pooling to the feature map."""
        feature_size = feature_map.shape[0]
        pool_output_size = feature_size // self.pool_size

        if pool_output_size < 1:
            raise ValueError("Feature map size too small for pooling operation!")

        pool_output = np.zeros((pool_output_size, pool_output_size))

        for i in range(0, feature_size - self.pool_size + 1, self.pool_size):
            for j in range(0, feature_size - self.pool_size + 1, self.pool_size):
                if i // self.pool_size < pool_output.shape[0] and j // self.pool_size < pool_output.shape[1]:
                    pool_output[i // self.pool_size, j // self.pool_size] = np.max(feature_map[i:i+self.pool_size, j:j+self.pool_size])

        return pool_output

class FullyConnectedLayer:
    def __init__(self, input_size, output_size):
        self.weights = np.random.randn(input_size, output_size)
        self.bias = np.zeros(output_size)

    def forward(self, input_data):
        """Perform the forward pass of the fully connected layer."""
        return np.dot(input_data, self.weights) + self.bias

class CNN:
    def __init__(self, filter_size=3, num_filters=8, pool_size=2, fc_size=10):
        self.conv_layer = ConvolutionalLayer(filter_size, num_filters)
        self.pooling_layer = PoolingLayer(pool_size)
        self.fc_layer = FullyConnectedLayer(num_filters * 4 * 4, fc_size)  # Adjusted for safety

    def forward(self, image):
        """Forward pass through the network (Conv + Pool + FC)."""
        conv_output = self.conv_layer.apply_filter(image)
        pooled_output = self.pooling_layer.apply_pooling(conv_output)

        flattened_output = pooled_output.flatten()

        # Ensure correct dimensionality
        if len(flattened_output) < self.fc_layer.weights.shape[0]:
            raise ValueError("Flattened output is smaller than expected for fully connected layer!")

        fc_output = self.fc_layer.forward(flattened_output)
        return fc_output

def cnn_example():
    """Example of using a simple CNN for image classification."""
    # Sample 10x10 image (increased size to prevent errors)
    image = np.random.rand(10, 10)

    # Initialize the CNN
    cnn = CNN(filter_size=3, num_filters=1, pool_size=2, fc_size=3)
    output = cnn.forward(image)

    print(f"Output of CNN: {output}")

# Example usage
cnn_example()
