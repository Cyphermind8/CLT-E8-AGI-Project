# Chunk 2: Advanced sorting algorithms and performance optimizations

def merge_sort(arr):
    """Sorts an array using the merge sort algorithm."""
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)

def merge(left, right):
    """Merges two sorted arrays into a single sorted array."""
    sorted_arr = []
    while left and right:
        if left[0] < right[0]:
            sorted_arr.append(left.pop(0))
        else:
            sorted_arr.append(right.pop(0))
    sorted_arr.extend(left or right)
    return sorted_arr

def quick_sort(arr):
    """Sorts an array using the quicksort algorithm."""
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)

def performance_optimization_example(data):
    """Optimizes performance for large data sets."""
    print("Starting optimization...")
    sorted_data = merge_sort(data)  # You can switch this to quick_sort for comparison
    print(f"Data sorted: {sorted_data[:10]}...")  # Print a small sample
    return sorted_data

# Example Usage
data = [34, 7, 23, 32, 5, 62, 32, 1, 13, 8]
optimized_data = performance_optimization_example(data)
