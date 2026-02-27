# 
# CS 440 Project 2  POSIX (pthreads) TEMPLATE
# Name(s):
# Michael Gavina
# Blake Karbon
# Date:
# 2/17/2026
# 
# we have attempted all three extra credits
# 
# 
# Goal: Implement 2.a / 2.b / 2.c so that EACH experiment creates/destroys
# exactly N_TOTAL threads (including all parent/initial/child/grandchild threads).
# 
# Includes:
#  - skeleton runners for 2.a, 2.b, 2.c (non-batched)
#  - skeleton runners for batching fallback
# 
# Students: Fill in TODO blocks. Keep printing sparse.
# 

import threading
import time
import sys

# ======= Fixed baseline (A, B, C must match) =======
N_TOTAL = 5000

# ======= 2.b parameters (must total exactly 5000) =======
# math: parents + parents*children_per_parent == 5000
# 50 + 50*99 = 50 + 4950 = 5000
B_PARENTS = 50
B_CHILDREN_PER_PARENT = 99

# ======= 2.c parameters (must total exactly 5000) =======
# math: initials + initials*children_per_initial + initials*children_per_initial*grandchildren_per_child == 5000
# 20 + 20*3 + 20*3*82 = 20 + 60 + 4920 = 5000
C_INITIALS = 20
C_CHILDREN_PER_INITIAL = 3
C_GRANDCHILDREN_PER_CHILD = 82

# ======= Batching knobs (reduce concurrency if needed) =======
A_BATCH_SIZE = 25
B_CHILD_BATCH_SIZE = 25
C_GRANDCHILD_BATCH_SIZE = 25

# ======= Counters =======
g_created = 0
g_destroyed = 0
counter_lock = threading.Lock()

def now_ns():
    return time.perf_counter_ns()

def reset_counts():
    global g_created, g_destroyed
    with counter_lock:
        g_created = 0
        g_destroyed = 0

def print_summary(label, start_ns, end_ns):
    elapsed_ms = (end_ns - start_ns) / 1e6
    with counter_lock:
        created = g_created
        destroyed = g_destroyed
    print(f"{label} elapsed: {elapsed_ms:.3f} ms")
    print(f"Threads created:   {created}")
    print(f"Threads destroyed: {destroyed}")

def atomic_inc_created():
    global g_created
    with counter_lock:
        g_created += 1

def atomic_inc_destroyed():
    global g_destroyed
    with counter_lock:
        g_destroyed += 1

# ============================================================
# 2.a – Flat workers
# ============================================================
def flat_worker():
    # minimal work
    atomic_inc_destroyed()

def run2a_flat_no_batching():
    print("\n=== 2.a Flat (no batching) ===")
    start = now_ns()
    
    threads = []
    for i in range(N_TOTAL):
        atomic_inc_created()
        t = threading.Thread(target=flat_worker)
        threads.append(t)
        t.start()
        if (i + 1) % 1000 == 0:
            print(f"Created threads: {i - 998}-{i + 1}")
            
    for i, t in enumerate(threads):
        t.join()
        if (i + 1) % 1000 == 0:
            print(f"Joined threads: {i - 998}-{i + 1}")
            
    end = now_ns()
    print_summary("2.a", start, end)
    return end-start

# ============================================================
# 2.b – Two-level hierarchy (parent -> children)
# ============================================================
def child_worker_2b():
    # minimal work
    atomic_inc_destroyed()

def parent_worker_2b_no_batching(parent_id):
    print(f"Parent {parent_id} started")
    
    children = []
    for i in range(B_CHILDREN_PER_PARENT):
        atomic_inc_created()
        t = threading.Thread(target=child_worker_2b)
        children.append(t)
        t.start()
        if (i + 1) % 25 == 0:
            print(f"Parent {parent_id} created children: {parent_id}-{i - 23} ... {parent_id}-{i + 1}")
            
    for t in children:
        t.join()
        
    atomic_inc_destroyed() # parent destroyed

def run2b_two_level_no_batching():
    print("\n=== 2.b Two-level (no batching) ===")
    start = now_ns()
    
    parents = []
    for i in range(B_PARENTS):
        atomic_inc_created()
        t = threading.Thread(target=parent_worker_2b_no_batching, args=(i + 1,))
        parents.append(t)
        t.start()
        
    for t in parents:
        t.join()
        
    end = now_ns()
    print_summary("2.b", start, end)
    return end-start

# ============================================================
# 2.c – Three-level hierarchy (initial -> child -> grandchild)
# ============================================================
def grandchild_worker_2c():
    atomic_inc_destroyed()

def child_worker_2c_no_batching(initial_id, child_id):
    grandkids = []
    for i in range(C_GRANDCHILDREN_PER_CHILD):
        atomic_inc_created()
        t = threading.Thread(target=grandchild_worker_2c)
        grandkids.append(t)
        t.start()
        if (i + 1) % 25 == 0:
            print(f"Child {initial_id}-{child_id} created grandchildren: {initial_id}-{child_id}-{i - 23} ... {initial_id}-{child_id}-{i + 1}")
            
    for t in grandkids:
        t.join()
    
    print(f"Child {initial_id}-{child_id} joined grandchildren: {initial_id}-{child_id}-1 ... {initial_id}-{child_id}-{C_GRANDCHILDREN_PER_CHILD}")
    print(f"Child {initial_id}-{child_id} completed")
    atomic_inc_destroyed()

def initial_worker_2c_no_batching(initial_id):
    print(f"Initial {initial_id} started")
    
    children = []
    for i in range(C_CHILDREN_PER_INITIAL):
        atomic_inc_created()
        t = threading.Thread(target=child_worker_2c_no_batching, args=(initial_id, i + 1))
        children.append(t)
        t.start()
        print(f"Initial {initial_id} created child: {initial_id}-{i + 1}")
        
    for t in children:
        t.join()
    
    print(f"Initial {initial_id} completed")
    atomic_inc_destroyed()

def run2c_three_level_no_batching():
    print("\n=== 2.c Three-level (no batching) ===")
    start = now_ns()
    
    initials = []
    for i in range(C_INITIALS):
        atomic_inc_created()
        t = threading.Thread(target=initial_worker_2c_no_batching, args=(i + 1,))
        initials.append(t)
        t.start()
        
    for t in initials:
        t.join()
        
    end = now_ns()
    print_summary("2.c", start, end)
    return end-start

# ============================================================
# main
# ============================================================
if __name__ == "__main__":
    # run 3 trials each if you want to follow the report requirement
    # but here we just call them once as in the C template's main.
    elapsedA = [];
    elapsedB = [];
    elapsedC = [];
    for i in range(3):
        print(f"Trial {i}:")
        reset_counts()
        elapsedA.append(run2a_flat_no_batching())
        
        reset_counts()
        elapsedB.append(run2b_two_level_no_batching())
        
        reset_counts()
        elapsedC.append(run2c_three_level_no_batching())

    
    avgAms = ((elapsedA[0] + elapsedA[1] + elapsedA[2])/3) / 1e6
    avgBms = ((elapsedB[0] + elapsedB[1] + elapsedB[2])/3) / 1e6
    avgCms = ((elapsedC[0] + elapsedC[1] + elapsedC[2])/3) / 1e6
    print("Averages:\n")
    print(f"Average 2.a elapsed: {avgAms} ms")
    print(f"Average 2.b elapsed: {avgBms} ms")
    print(f"Average 2.c elapsed: {avgCms} ms")
