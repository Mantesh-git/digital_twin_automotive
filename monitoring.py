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