"""
Module 01 - Step 2: Fundamentals of Asynchronous Python (`asyncio`).

This lab breaks down asynchronous programming from the ground up for software engineers
and data engineers transitioning to `asyncio` or building high-throughput services.

========================================================================================
1. MENTAL MODEL: SYNCHRONOUS VS. ASYNCHRONOUS EXECUTION
========================================================================================

Imagine a waiter in a busy restaurant:

  - SYNCHRONOUS WAITER (Blocking):
    Takes Order from Table 1 -> walks to kitchen -> STANDS STILL IN KITCHEN WAITING 5 MINS
    for food -> delivers food to Table 1. ONLY THEN moves to Table 2.
    Total time for 3 tables = 5m + 5m + 5m = 15 minutes.

  - ASYNCHRONOUS WAITER (Cooperative Event Loop):
    Takes Order from Table 1 -> sends to kitchen -> IMMEDIATELY walks to Table 2 while
    kitchen cooks Order 1 -> Takes Order from Table 2 -> sends to kitchen...
    When kitchen bell rings for Order 1, waiter picks up and serves Table 1.
    Total time for 3 tables = ~5 minutes (the time of the longest cook operation!).

========================================================================================
2. KEY ARCHITECTURAL CONCEPTS & TERMINOLOGY
========================================================================================

1. Single-Threaded Event Loop:
   - Python `asyncio` runs in a SINGLE thread by default.
   - It does NOT achieve concurrency via OS multi-threading or multi-processing (CPU cores).
   - Concurrency is achieved via COOPERATIVE MULTITASKING: tasks voluntarily yield control
     back to the Event Loop when waiting for I/O (network requests, disk reads, timers).

2. I/O-Bound vs CPU-Bound Operations:
   - EXCELLENT FOR ASYNC: I/O-bound work (HTTP calls, DB queries, file operations, web sockets).
     While waiting for network bytes, CPU sits idle—perfect for switching tasks.
   - NOT FOR ASYNC: CPU-bound work (matrix multiplication, image processing, video encoding).
     Synchronous CPU calculations will BLOCK the single thread and freeze the Event Loop!
     (For CPU-bound tasks, use `ProcessPoolExecutor` or `asyncio.to_thread()`).

3. Core Vocabulary:
   - Coroutine Function (`async def`): A function definition capable of yielding control.
   - Coroutine Object: The object returned when calling a coroutine function. Not executed yet!
   - `await`: Key statement that pauses execution of current coroutine until result is ready,
     handing control back to the Event Loop to run other ready tasks.
   - Task (`asyncio.create_task`): A wrapper around a coroutine scheduled to run on the Event Loop concurrently.
   - Event Loop: The underlying engine managing queue of tasks, polling OS I/O notifications,
     and switching execution contexts.

========================================================================================
4. DEMO BREAKDOWN
========================================================================================
1. Synchronous Simulation: Illustrates blocking sequential bottlenecks (`time.sleep`).
2. Coroutine & Await Basics: Explains `async def`, coroutine object instantiation, and `await`.
3. Concurrent Tasks (`asyncio.create_task`): Shows how background task scheduling yields speedups.
"""

import asyncio
import time
import logging

# Configure readable structured logging with timestamps
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


# ===================================================================
# 1. Synchronous Simulation (Blocking I/O)
# ===================================================================
def sync_fetch_document(doc_id: str, delay: float = 0.2) -> str:
    """
    Simulates a traditional synchronous HTTP API request or database fetch.
    
    UNDER THE HOOD:
    `time.sleep()` is a blocking OS call. It forces the current OS thread to sleep,
    preventing ANY other code from running on this thread during the delay window.
    """
    logging.info(f"[SYNC] Starting fetch for {doc_id}...")
    time.sleep(delay)  # Block thread completely
    logging.info(f"[SYNC] Completed fetch for {doc_id}")
    return f"Content of {doc_id}"


def run_synchronous_demo():
    """
    Demonstrates sequential blocking execution.
    
    Total time = sum of all individual delays:
    t_total = delay_1 + delay_2 + delay_3
    """
    print("\n--- 1. Synchronous Batch Execution ---")
    start = time.perf_counter()
    
    # Each call must finish completely before the next line of code begins.
    res1 = sync_fetch_document("doc_1", 0.2)
    res2 = sync_fetch_document("doc_2", 0.2)
    res3 = sync_fetch_document("doc_3", 0.2)
    
    elapsed = time.perf_counter() - start
    print(f"Sync Execution Total Time: {elapsed:.3f} seconds (0.2s * 3 = 0.6s sequential)")


# ===================================================================
# 2. Asynchronous Simulation (Non-Blocking I/O)
# ===================================================================
async def async_fetch_document(doc_id: str, delay: float = 0.2) -> str:
    """
    Asynchronous Coroutine Function.
    
    Key Elements:
    1. `async def`: Marks function as a coroutine. Calling it returns a coroutine object.
    2. `await asyncio.sleep(delay)`: NON-BLOCKING pause.
       Unlike `time.sleep()`, `asyncio.sleep()` creates a timer in the Event Loop
       and yields control back to the loop. The Event Loop can switch to execute
       other ready coroutines while this timer counts down.
    """
    logging.info(f"[ASYNC] Starting fetch for {doc_id}...")
    await asyncio.sleep(delay)  # Non-blocking pause: yields control to Event Loop
    logging.info(f"[ASYNC] Completed fetch for {doc_id}")
    return f"Async Content of {doc_id}"


async def run_coroutine_basics_demo():
    """
    Demonstrates the fundamental behavior of coroutine instantiation and execution.
    
    LESSON:
    Calling `async def func()` DOES NOT start execution! It creates a suspended coroutine object.
    You MUST `await` the coroutine object (or wrap it in a Task) to execute it.
    """
    print("\n--- 2. Coroutine & Await Basics ---")
    
    # Step 1: Call `async def` function directly.
    # Note: Code inside `async_fetch_document` has NOT started running yet!
    coro_object = async_fetch_document("doc_demo", 0.1)
    print(f"Calling async def directly yields a coroutine object: {coro_object}")

    # Step 2: `await` the coroutine object.
    # The `await` keyword hands the coroutine object to the Event Loop, executes it,
    # suspends execution here until complete, and retrieves the returned value.
    result = await coro_object
    print(f"Awaited result: {result}")


async def run_concurrent_tasks_demo():
    """
    Demonstrates true concurrent task execution using `asyncio.create_task()`.
    
    HOW IT WORKS:
    1. `asyncio.create_task(coro)` wraps the coroutine in a `Task` object.
    2. It IMMEDIATELY registers the task with the active Event Loop, scheduling it
       to start running in the background on the next Event Loop tick.
    3. All 3 tasks begin execution concurrently when the event loop gains control.
    4. `await task1` suspends `run_concurrent_tasks_demo` until task1 completes, but
       tasks 2 & 3 continue running concurrently in the background.
    
    TIME COMPARISON:
    Instead of 0.2s + 0.2s + 0.2s = 0.6s, all 3 run during the SAME 0.2s window!
    Total time ≈ max(delay_1, delay_2, delay_3) ≈ 0.2s.
    """
    print("\n--- 3. Concurrent Task Execution with `asyncio.create_task` ---")
    start = time.perf_counter()

    # Schedule 3 coroutines to run on the event loop concurrently in the background
    task1 = asyncio.create_task(async_fetch_document("doc_1", 0.2))
    task2 = asyncio.create_task(async_fetch_document("doc_2", 0.2))
    task3 = asyncio.create_task(async_fetch_document("doc_3", 0.2))

    # Await results of background tasks.
    # Note: Even while awaiting task1, task2 and task3 are active in the Event Loop background.
    r1 = await task1
    r2 = await task2
    r3 = await task3

    elapsed = time.perf_counter() - start
    print(f"Async Execution Total Time: {elapsed:.3f} seconds (~0.2s concurrent!)")
    print(f"Results: {[r1, r2, r3]}")
    
    # Note: For gathering lists of dynamic tasks, prefer `asyncio.gather(*tasks)` or
    # `asyncio.TaskGroup()` (Python 3.11+).


# ===================================================================
# 4. Entry Point & Event Loop Orchestration
# ===================================================================
async def main():
    """
    Main asynchronous entrypoint function combining all demonstration modules.
    """
    print("=" * 60)
    print("STEP 2: ASYNCIO FUNDAMENTALS & MENTAL MODEL")
    print("=" * 60)

    # Demo 1: Synchronous blocking sequential execution
    run_synchronous_demo()

    # Demo 2: Coroutine object creation vs awaiting
    await run_coroutine_basics_demo()

    # Demo 3: Concurrent task execution with event loop scheduling
    await run_concurrent_tasks_demo()


if __name__ == "__main__":
    """
    `asyncio.run(main())` is the standard entry point for an asyncio program.
    
    UNDER THE HOOD (`asyncio.run` lifecycle):
    1. Creates a brand new Event Loop.
    2. Sets the new loop as the current thread's active event loop.
    3. Runs the passed coroutine (`main()`) until it completes.
    4. Cancels any lingering scheduled tasks and closes async generators.
    5. Cleanly closes the Event Loop upon completion.
    
    BEST PRACTICE:
    - Call `asyncio.run()` ONLY ONCE as the root entry point of your application script.
    - Do not call `asyncio.run()` inside an existing event loop (e.g. within web server handlers).
    """
    asyncio.run(main())

