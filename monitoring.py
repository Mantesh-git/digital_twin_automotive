import timeit
import cProfile
import pstats
import tracemalloc
import io
import logging

logger = logging.getLogger(__name__)


def measure_time(func, *args, runs=3, label=""):
    # Run the function multiple times and log the average execution time
    name = label or func.__name__
    total = timeit.timeit(lambda: func(*args), number=runs)
    avg = round(total / runs, 4)
    logger.info("%s - avg time: %ss over %d runs", name, avg, runs)
    return avg


def measure_memory(func, *args, label=""):
    # Track memory usage while the function runs using tracemalloc
    name = label or func.__name__
    tracemalloc.start()
    result = func(*args)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    logger.info("%s - current memory: %.1f KB, peak: %.1f KB",
                name, current / 1024, peak / 1024)
    return result


def profile_function(func, *args):
    # Use cProfile to find which parts of the function take the most time
    profiler = cProfile.Profile()
    profiler.enable()
    result = func(*args)
    profiler.disable()

    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats("cumulative")
    stats.print_stats(10)
    logger.info("cProfile result:\n%s", stream.getvalue())
    return result


def compare_approaches(func1, func2, args1=(), args2=(), runs=3):
    # Compare two functions and show which is faster
    t1 = timeit.timeit(lambda: func1(*args1), number=runs)
    t2 = timeit.timeit(lambda: func2(*args2), number=runs)

    faster = func2.__name__ if t2 < t1 else func1.__name__
    ratio  = round(max(t1, t2) / min(t1, t2), 1)

    logger.info("Comparison over %d runs:", runs)
    logger.info("  %s: %.4fs", func1.__name__, t1)
    logger.info("  %s: %.4fs", func2.__name__, t2)
    logger.info("  %s is %sx faster", faster, ratio)

    print(f"\nComparison ({runs} runs):")
    print(f"  {func1.__name__:30} - {t1:.4f}s")
    print(f"  {func2.__name__:30} - {t2:.4f}s")
    print(f"  {faster} is {ratio}x faster")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s | %(levelname)s | %(message)s")

    sample = list(range(10000))

    # O(n2) approach — slow, nested loop
    def find_duplicates_slow(data):
        return [x for x in data if data.count(x) > 1]

    # O(n) approach — fast, uses set
    def find_duplicates_fast(data):
        seen, dupes = set(), set()
        for x in data:
            if x in seen:
                dupes.add(x)
            seen.add(x)
        return list(dupes)

    print("Test 1 - timeit")
    measure_time(find_duplicates_fast, sample, runs=3, label="find_duplicates_fast")

    print("\nTest 2 - compare O(n2) vs O(n)")
    small = list(range(1000))
    compare_approaches(
        find_duplicates_slow,
        find_duplicates_fast,
        args1=(small,),
        args2=(small,),
        runs=3
    )

    print("\nTest 3 - tracemalloc")
    def load_all(data):
        return [x * 2 for x in data]

    def load_generator(data):
        return list(x * 2 for x in data)

    measure_memory(load_all,       sample, label="load_all_at_once")
    measure_memory(load_generator, sample, label="load_with_generator")

    print("\nTest 4 - cProfile")
    profile_function(find_duplicates_fast, small)

    print("\nAll tests passed")