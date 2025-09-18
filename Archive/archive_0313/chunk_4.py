# Chunk 4: Implementing a simple neural network for classification

import random
import math

class NeuralNetwork:
    def __init__(self, input_size, hidden_size, output_size):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size

        # Initialize weights
        self.weights_input_hidden = [[random.uniform(-1, 1) for _ in range(hidden_size)] for _ in range(input_size)]
        self.weights_hidden_output = [[random.uniform(-1, 1) for _ in range(output_size)] for _ in range(hidden_size)]

        # Initialize biases
        self.bias_hidden = [random.uniform(-1, 1) for _ in range(hidden_size)]
        self.bias_output = [random.uniform(-1, 1) for _ in range(output_size)]

    def sigmoid(self, x):
        """Sigmoid activation function."""
        return 1 / (1 + math.exp(-x))

    def sigmoid_derivative(self, x):
        """Derivative of the sigmoid function."""
        return x * (1 - x)

    def feedforward(self, inputs):
        """Feedforward pass through the network."""
        # Input to hidden layer
        hidden_input = [sum([inputs[i] * self.weights_input_hidden[i][j] for i in range(self.input_size)]) + self.bias_hidden[j] for j in range(self.hidden_size)]
        hidden_output = [self.sigmoid(x) for x in hidden_input]

        # Hidden to output layer
        output_input = [sum([hidden_output[j] * self.weights_hidden_output[j][k] for j in range(self.hidden_size)]) + self.bias_output[k] for k in range(self.output_size)]
        output = [self.sigmoid(x) for x in output_input]

        return hidden_output, output  # Return both hidden and output layers

    def train(self, inputs, targets, learning_rate=0.1, epochs=10000):
        """Train the neural network using backpropagation."""
        for epoch in range(epochs):
            # Feedforward
            hidden_output, output = self.feedforward(inputs)

            # Calculate errors
            output_errors = [targets[i] - output[i] for i in range(self.output_size)]
            hidden_errors = [sum([output_errors[i] * self.weights_hidden_output[j][i] for i in range(self.output_size)]) for j in range(self.hidden_size)]

            # Backpropagation
            for i in range(self.output_size):
                for j in range(self.hidden_size):
                    self.weights_hidden_output[j][i] += learning_rate * output_errors[i] * self.sigmoid_derivative(output[i]) * hidden_output[j]

                self.bias_output[i] += learning_rate * output_errors[i] * self.sigmoid_derivative(output[i])

            for j in range(self.hidden_size):
                for i in range(self.input_size):
                    self.weights_input_hidden[i][j] += learning_rate * hidden_errors[j] * self.sigmoid_derivative(hidden_output[j]) * inputs[i]

                self.bias_hidden[j] += learning_rate * hidden_errors[j] * self.sigmoid_derivative(hidden_output[j])

def neural_network_example():
    """Example of training and using a simple neural network."""
    # Sample input data: [input1, input2]
    inputs = [0.5, 0.8]
    targets = [1]  # Desired output

    nn = NeuralNetwork(input_size=2, hidden_size=3, output_size=1)
    nn.train(inputs, targets)

    hidden_output, output = nn.feedforward(inputs)
    print(f"Predicted output: {output}")

# Example usage
neural_network_example()
