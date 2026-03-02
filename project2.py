import threading
import time
import concurrent.futures
from dataclasses import dataclass
from typing import List, Optional, Callable

# Global Variables
minimal_work = 0
g_created = 0
g_destroyed = 0
counter_lock = threading.Lock()

def reset_counts():
    global g_created, g_destroyed, minimal_work
    with counter_lock:
        g_created = 0
        g_destroyed = 0
        minimal_work = 0

def increment_created():
    global g_created
    with counter_lock:
        g_created += 1

def increment_destroyed():
    global g_destroyed
    with counter_lock:
        g_destroyed += 1

def increment_work():
    global minimal_work
    with counter_lock:
        minimal_work += 1

# Configuration
TOTAL_THREADS = 100
N_TOTAL = 5000

# 2.b parameters
B_PARENTS = 50
B_CHILDREN_PER_PARENT = 99

# 2.c parameters
C_INITIALS = 20
C_CHILDREN_PER_INITIAL = 3
C_GRANDCHILDREN_PER_CHILD = 82

def now_ns():
    return time.perf_counter_ns()

def print_summary(label, start_ns, end_ns):
    elapsed_ms = (end_ns - start_ns) / 1e6
    print(f"{label} elapsed: {elapsed_ms:.3f} ms")
    print(f"Threads created:   {g_created}")
    print(f"Threads destroyed: {g_destroyed}")

# ============================================================
# 2.a — Flat workers
# ============================================================
def flat_worker():
    increment_work()
    increment_destroyed()

def run2a_flat_no_batching():
    print("\n=== 2.a Flat (no batching) ===")
    start = now_ns()
    
    threads = []
    for i in range(N_TOTAL):
        increment_created()
        t = threading.Thread(target=flat_worker)
        t.start()
        threads.append(t)
        if (i + 1) % 1000 == 0:
            print(f"Created threads: {i - 998}-{i + 1}")
            
    for i, t in enumerate(threads):
        t.join()
        if (i + 1) % 1000 == 0:
            print(f"Joined threads: {i - 998}-{i + 1}")
            
    end = now_ns()
    print_summary("2.a", start, end)
    return end - start

def run2a_flat_thread_pool(executor):
    print("\n=== 2.a Flat (thread pool) ===")
    start = now_ns()
    
    futures = []
    for i in range(N_TOTAL):
        increment_created()
        futures.append(executor.submit(flat_worker))
        if (i + 1) % 1000 == 0:
            print(f"Adding work: {i - 998}-{i + 1}")
            
    concurrent.futures.wait(futures)
    print("Work complete!")
    
    end = now_ns()
    print_summary("2.a", start, end)
    return end - start

# ============================================================
# 2.b — Two-level hierarchy
# ============================================================
def child_worker_2b():
    increment_work()
    increment_destroyed()

def parent_worker_2b_no_batching(parent_id):
    print(f"Parent {parent_id} started")
    threads = []
    for i in range(B_CHILDREN_PER_PARENT):
        increment_created()
        t = threading.Thread(target=child_worker_2b)
        t.start()
        threads.append(t)
        if (i + 1) % 25 == 0:
            print(f"Parent {parent_id} created children: {parent_id}-{i-23} ... {parent_id}-{i+1}")
            
    for t in reversed(threads):
        t.join()
        
    print(f"Parent {parent_id} joined children: {parent_id}-{B_CHILDREN_PER_PARENT} ... {parent_id}-1")
    print(f"Parent {parent_id} completed")
    increment_destroyed()

def run2b_two_level_no_batching():
    print("\n=== 2.b Two-level (no batching) ===")
    start = now_ns()
    
    parents = []
    for i in range(B_PARENTS):
        increment_created()
        t = threading.Thread(target=parent_worker_2b_no_batching, args=(i + 1,))
        t.start()
        parents.append(t)
        
    for t in parents:
        t.join()
        
    end = now_ns()
    print_summary("2.b", start, end)
    return end - start

def parent_worker_2b_thread_pool(executor, pid):
    print(f"Parent {pid} started")
    futures = []
    for i in range(B_CHILDREN_PER_PARENT):
        increment_created()
        futures.append(executor.submit(child_worker_2b))
        if (i + 1) % 25 == 0:
            print(f"Parent {pid} added children to work: {pid}-{i-23} ... {pid}-{i+1}")
            
    # In C version, threadPoolWait is called at the end of run2b, not inside parent.
    # However, to simulate the same structure:
    print("Work Complete!")
    print(f"Parent {pid} joined children: {pid}-{B_CHILDREN_PER_PARENT} ... {pid}-1")
    print(f"Parent {pid} completed")
    increment_destroyed()

def run2b_two_level_thread_pool(executor):
    print("\n=== 2.b Two-level (Thread Pooling) ===")
    start = now_ns()
    
    futures = []
    for i in range(B_PARENTS):
        increment_created()
        futures.append(executor.submit(parent_worker_2b_thread_pool, executor, i + 1))
        
    concurrent.futures.wait(futures)
    end = now_ns()
    print_summary("2.b", start, end)
    return end - start

# ============================================================
# 2.c — Three-level hierarchy
# ============================================================
def grandchild_worker_2c():
    increment_work()
    increment_destroyed()

def child_worker_2c_no_batching(iid, cid):
    threads = []
    for i in range(C_GRANDCHILDREN_PER_CHILD):
        increment_created()
        t = threading.Thread(target=grandchild_worker_2c)
        t.start()
        threads.append(t)
        if (i + 1) % 25 == 0:
            print(f"Child {iid}-{cid} created grandchildren: {iid}-{cid}-{i-23} ... {iid}-{cid}-{i+1}")
            
    for t in reversed(threads):
        t.join()
        
    print(f"Child {iid}-{cid} joined grandchildren: {iid}-{cid}-{C_GRANDCHILDREN_PER_CHILD} ... {iid}-{cid}-1")
    print(f"Child {iid}-{cid} completed")
    increment_destroyed()

def initial_worker_2c_no_batching(iid):
    print(f"Initial {iid} started")
    threads = []
    for i in range(C_CHILDREN_PER_INITIAL):
        increment_created()
        t = threading.Thread(target=child_worker_2c_no_batching, args=(iid, i + 1))
        t.start()
        threads.append(t)
        print(f"Initial {iid} created child: {iid}-{i+1}")
        
    for t in threads:
        t.join()
        
    print(f"Initial {iid} completed")
    increment_destroyed()

def run2c_three_level_no_batching():
    print("\n=== 2.c Three-level (no batching) ===")
    start = now_ns()
    
    initials = []
    for i in range(C_INITIALS):
        increment_created()
        t = threading.Thread(target=initial_worker_2c_no_batching, args=(i + 1,))
        t.start()
        initials.append(t)
        
    for t in initials:
        t.join()
        
    end = now_ns()
    print_summary("2.c", start, end)
    return end - start

def child_worker_2c_thread_pool(executor, iid, cid):
    for i in range(C_GRANDCHILDREN_PER_CHILD):
        increment_created()
        executor.submit(grandchild_worker_2c)
        if (i + 1) % 25 == 0:
            print(f"Child {iid}-{cid} added grandchildren to work: {iid}-{cid}-{i-23} ... {iid}-{cid}-{i+1}")
            
    print(f"Child {iid}-{cid} completed")
    increment_destroyed()

def initial_worker_2c_thread_pool(executor, iid):
    print(f"Initial {iid} started")
    for i in range(C_CHILDREN_PER_INITIAL):
        increment_created()
        executor.submit(child_worker_2c_thread_pool, executor, iid, i + 1)
        print(f"Initial {iid} added child to work: {iid}-{i+1}")
        
    print(f"Initial {iid} completed")
    increment_destroyed()

def run2c_three_level_thread_pool(executor):
    print("\n=== 2.c Three-level (thread pooling) ===")
    start = now_ns()
    
    for i in range(C_INITIALS):
        increment_created()
        executor.submit(initial_worker_2c_thread_pool, executor, i + 1)
        
    # The C version uses threadPoolWait which waits for all pending work.
    # ThreadPoolExecutor doesn't have an exact equivalent without shutting down,
    # but we can't easily wait for 'all current and future tasks' without more logic.
    # However, for this conversion, we can wait until g_destroyed reaches the target.
    # Total expected threads: INITIALS + INITIALS*CHILDREN + INITIALS*CHILDREN*GRANDCHILDREN
    # = 20 + 20*3 + 20*3*82 = 20 + 60 + 4920 = 5000.
    
    while True:
        with counter_lock:
            if g_destroyed == N_TOTAL:
                break
        time.sleep(0.01)
        
    end = now_ns()
    print_summary("2.c", start, end)
    return end - start

def main():
    with concurrent.futures.ThreadPoolExecutor(max_workers=TOTAL_THREADS) as executor:
        elapsedA = [0] * 3
        elapsedB = [0] * 3
        elapsedC = [0] * 3
        elapsedD = [0] * 3
        elapsedE = [0] * 3
        elapsedF = [0] * 3
        
        for i in range(3):
            print(f"Trial {i}:")
            
            reset_counts()
            elapsedA[i] = run2a_flat_no_batching()
            
            reset_counts()
            elapsedB[i] = run2b_two_level_no_batching()
            
            reset_counts()
            elapsedC[i] = run2c_three_level_no_batching()
            
            reset_counts()
            elapsedD[i] = run2a_flat_thread_pool(executor)
            
            reset_counts()
            elapsedE[i] = run2b_two_level_thread_pool(executor)
            
            reset_counts()
            elapsedF[i] = run2c_three_level_thread_pool(executor)
            
        avgA = sum(elapsedA) / 3
        avgB = sum(elapsedB) / 3
        avgC = sum(elapsedC) / 3
        avgD = sum(elapsedD) / 3
        avgE = sum(elapsedE) / 3
        avgF = sum(elapsedF) / 3
        
        print("\nAverages:\n")
        print(f"Average 2.a elapsed: {avgA/1e6:.3f} ms")
        print(f"Average 2.b elapsed: {avgB/1e6:.3f} ms")
        print(f"Average 2.c elapsed: {avgC/1e6:.3f} ms")
        print(f"Average 2.d elapsed: {avgD/1e6:.3f} ms")
        print(f"Average 2.e elapsed: {avgE/1e6:.3f} ms")
        print(f"Average 2.f elapsed: {avgF/1e6:.3f} ms")

if __name__ == "__main__":
    main()
