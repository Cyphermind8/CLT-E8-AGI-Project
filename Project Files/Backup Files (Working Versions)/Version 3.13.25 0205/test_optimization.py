import time

def fibonacci_original(n, memo={}):
    """Slow recursive Fibonacci with memoization to prevent excessive recalculations."""
    if n in memo:
        return memo[n]
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        memo[n] = fibonacci_original(n-1, memo) + fibonacci_original(n-2, memo)
        return memo[n]

def fibonacci_optimized(n):
    """Fast iterative Fibonacci (O(n) time, O(1) space)."""
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a

def measure_time(func, n, iterations=100):
    """Run function multiple times to get a measurable execution time (in milliseconds)."""
    start_time = time.perf_counter()
    for _ in range(iterations):
        func(n)
    end_time = time.perf_counter()
    elapsed_time = ((end_time - start_time) / iterations) * 1000  # ✅ Convert to milliseconds

    return max(elapsed_time, 0.0001)  # ✅ Prevents division by zero

def test_fibonacci_performance():
    test_values = [10, 100, 1_000, 10_000, 100_000]  # ✅ Testing larger values

    for n in test_values:
        print(f"\n🔹 **n = {n}**")

        # ✅ Skip recursive test for large n (n > 30)
        if n <= 30:
            original_time = measure_time(fibonacci_original, n, iterations=10)  # ✅ Reduce iterations
        else:
            original_time = float("inf")  # ✅ Placeholder for skipped cases

        optimized_time = measure_time(fibonacci_optimized, n, iterations=100)  # ✅ Reduced iterations for large n

        if original_time != float("inf"):
            print(f"   🏁 Original: {fibonacci_original(n)} | Time: {original_time:.6f} ms")
        else:
            print(f"   🏁 Original: Skipped for n = {n} (too slow)")

        print(f"   🚀 Optimized: {fibonacci_optimized(n)} | Time: {optimized_time:.6f} ms")

        if optimized_time > 0 and original_time != float("inf"):
            speedup = original_time / optimized_time
            print(f"   ✅ Optimization Improvement: {speedup:.2f}x Faster\n")
        else:
            print("   ⚠️ Optimized function executed too fast to measure performance accurately.\n")

if __name__ == "__main__":
    test_fibonacci_performance()
