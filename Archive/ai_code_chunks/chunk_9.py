# Chunk 9: AI-Based Data Clustering (K-Means Algorithm)

import numpy as np
import random

class KMeans:
    """K-Means clustering algorithm."""
    def __init__(self, num_clusters, max_iterations=100):
        self.num_clusters = num_clusters
        self.max_iterations = max_iterations

    def initialize_centroids(self, data):
        """Randomly initialize cluster centroids."""
        return random.sample(list(data), self.num_clusters)

    def assign_clusters(self, data, centroids):
        """Assign each data point to the nearest cluster centroid."""
        clusters = [[] for _ in range(self.num_clusters)]
        for point in data:
            distances = [np.linalg.norm(point - centroid) for centroid in centroids]
            cluster_index = np.argmin(distances)
            clusters[cluster_index].append(point)
        return clusters

    def update_centroids(self, clusters):
        """Compute new centroids as the mean of each cluster."""
        return [np.mean(cluster, axis=0) if cluster else np.random.rand(2) for cluster in clusters]

    def fit(self, data):
        """Train the K-Means model."""
        centroids = self.initialize_centroids(data)
        for _ in range(self.max_iterations):
            clusters = self.assign_clusters(data, centroids)
            new_centroids = self.update_centroids(clusters)
            if np.allclose(centroids, new_centroids):
                break  # Convergence reached
            centroids = new_centroids
        return centroids, clusters

def kmeans_example():
    """Example usage of K-Means clustering."""
    data = np.random.rand(50, 2)  # Generate random 2D points
    kmeans = KMeans(num_clusters=3)
    centroids, clusters = kmeans.fit(data)
    print(f"Final cluster centroids: {centroids}")

# Example usage
kmeans_example()
