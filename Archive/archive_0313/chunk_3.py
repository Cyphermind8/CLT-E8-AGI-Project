# Chunk 3: AI model for decision-making and optimization

class DecisionTreeNode:
    def __init__(self, value=None):
        self.value = value
        self.left = None
        self.right = None

    def insert(self, value):
        """Insert a value into the tree."""
        if self.value is None:
            self.value = value
        elif value < self.value:
            if self.left is None:
                self.left = DecisionTreeNode(value)
            else:
                self.left.insert(value)
        else:
            if self.right is None:
                self.right = DecisionTreeNode(value)
            else:
                self.right.insert(value)

    def search(self, value):
        """Search for a value in the tree."""
        if self.value is None or self.value == value:
            return self
        elif value < self.value and self.left is not None:
            return self.left.search(value)
        elif value > self.value and self.right is not None:
            return self.right.search(value)
        return None

def build_decision_tree(values):
    """Build a decision tree from a list of values."""
    if not values:
        return None
    root = DecisionTreeNode(values[0])
    for value in values[1:]:
        root.insert(value)
    return root

def decision_tree_optimization_example():
    """Example of using a decision tree to optimize decision-making."""
    data = [15, 10, 20, 25, 30, 5, 7, 3, 8]
    root = build_decision_tree(data)

    print("Decision Tree constructed.")
    print("Searching for 7 in the tree:", root.search(7).value)  # Should return 7
    print("Searching for 50 in the tree:", root.search(50))  # Should return None

# Example usage
decision_tree_optimization_example()
