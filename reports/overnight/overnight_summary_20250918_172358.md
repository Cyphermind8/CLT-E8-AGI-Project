# Overnight Summary — 20250918_172358

- Runs analyzed: **131**
- Pass rate min/median/max: **83.3% / 100.0% / 100.0%**
- Median avg-latency per run: **4.154s**

## Recent runs
| timestamp | passed/total | pass rate | avg latency (s) | deterministic | report |
|---|---:|---:|---:|:---:|:---|
| 20250918_171432 | 12/12 | 100.0% | 3.484 | ✅ | bench_20250918_171432.json |
| 20250918_170807 | 12/12 | 100.0% | 4.216 | ✅ | bench_20250918_170807.json |
| 20250918_170125 | 12/12 | 100.0% | 4.234 | ✅ | bench_20250918_170125.json |
| 20250918_165443 | 12/12 | 100.0% | 4.207 | ✅ | bench_20250918_165443.json |
| 20250918_164801 | 12/12 | 100.0% | 4.241 | ✅ | bench_20250918_164801.json |
| 20250918_164118 | 12/12 | 100.0% | 4.064 | ✅ | bench_20250918_164118.json |
| 20250918_163439 | 12/12 | 100.0% | 3.947 | ✅ | bench_20250918_163439.json |
| 20250918_162804 | 12/12 | 100.0% | 4.06 | ✅ | bench_20250918_162804.json |
| 20250918_162125 | 12/12 | 100.0% | 4.01 | ✅ | bench_20250918_162125.json |
| 20250918_161448 | 12/12 | 100.0% | 4.141 | ✅ | bench_20250918_161448.json |

## Flaky tests (pass and fail across runs)
- json_merge
- json_sort_values

## Slowest tests across runs (avg latency)
| test | avg latency (s) |
|---|---:|
| fib_20 | 7.738 |
| json_uppercase | 7.669 |
| reverse_digits | 5.705 |
| extract_year | 4.429 |
| json_sort_values | 3.552 |

## Recent failure messages (first occurrence)
- **json_sort_values** — `got an unexpected keyword argument 'key'`
- **json_merge** — `got an unexpected keyword argument 'a'`
