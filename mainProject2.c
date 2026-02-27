/*
 * CS 440 Project 2 — POSIX (pthreads) TEMPLATE
 * Name(s):
 * Michael Gavina
 * Blake Karbon
 * Date:
 * 2/17/2026
 * 
 * we have attempted all three extra credits
 *
 *
 * Goal: Implement 2.a / 2.b / 2.c so that EACH experiment creates/destroys
 * exactly N_TOTAL threads (including all parent/initial/child/grandchild threads).
 *
 * Includes:
 *  - skeleton runners for 2.a, 2.b, 2.c (non-batched)
 *  - skeleton runners for batching fallback
 *
 * Students: Fill in TODO blocks. Keep printing sparse.
 *
 * Build:
 *   gcc mainProject2.c -o mainProject2
 */

#define _POSIX_C_SOURCE 200809L

#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdatomic.h>
#include <time.h>
#include <errno.h>
#include <string.h>

// ======= Fixed baseline (A, B, C must match) =======
enum { N_TOTAL = 5000 };

// ======= 2.b parameters (must total exactly 5000) =======
// TODO: verify math: parents + parents*children_per_parent == 5000
enum { B_PARENTS = 50, B_CHILDREN_PER_PARENT = 99 };

// ======= 2.c parameters (must total exactly 5000) =======
// TODO: verify math:
// initials + initials*children_per_initial + initials*children_per_initial*grandchildren_per_child == 5000
enum { C_INITIALS = 20, C_CHILDREN_PER_INITIAL = 3, C_GRANDCHILDREN_PER_CHILD = 82 };

// ======= Batching knobs (reduce concurrency if needed) =======
enum { A_BATCH_SIZE = 25, B_CHILD_BATCH_SIZE = 25, C_GRANDCHILD_BATCH_SIZE = 25 };

// ======= Counters =======
static atomic_int g_created = 0;
static atomic_int g_destroyed = 0;

// ------------------------------------------------------------
// Timing (POSIX monotonic clock)
// ------------------------------------------------------------
static long long now_ns(void) {
    struct timespec ts;
    // TODO: handle error if clock_gettime fails (rare)
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) {
        perror("clock_gettime");
        exit(EXIT_FAILURE);
    }
    //clock_gettime(CLOCK_MONOTONIC, &ts); We dont need this
    return (long long)ts.tv_sec * 1000000000LL + (long long)ts.tv_nsec;
}

static void reset_counts(void) {
    atomic_store(&g_created, 0);
    atomic_store(&g_destroyed, 0);
}

static void print_summary(const char *label, long long start_ns, long long end_ns) {
    double elapsed_ms = (end_ns - start_ns) / 1e6;
    printf("%s elapsed: %.3f ms\n", label, elapsed_ms);
    printf("Threads created:   %d\n", atomic_load(&g_created));
    printf("Threads destroyed: %d\n", atomic_load(&g_destroyed));
}

// ------------------------------------------------------------
// Error helper
// ------------------------------------------------------------
static void die_pthread(int rc, const char *where) {
    if (rc == 0) return;
    fprintf(stderr, "ERROR: %s: %s\n", where, strerror(rc));
    exit(EXIT_FAILURE);
}

// ============================================================
// 2.a — Flat workers
// ============================================================
typedef struct {
    int id; // optional
} flat_arg_t;

static void *flat_worker(void *arg) {
    (void)arg;
    // TODO: optional minimal work
    // TODO: optional sparse print using id
    atomic_fetch_add(&g_destroyed, 1);
    return NULL;
}

// ============================================================
// 2.a — Flat (no batching)
// ============================================================
static long long run2a_flat_no_batching(void) {
    printf("\n=== 2.a Flat (no batching) ===\n");
    int rc;
    long long start = now_ns();

    pthread_t *ths = malloc(sizeof(pthread_t) * N_TOTAL);
    if (!ths) { perror("malloc"); exit(1); }

    // TODO: allocate pthread_t array of size N_TOTAL
    // pthread_t *ths = malloc(sizeof(*ths) * N_TOTAL);
    // TODO: optionally allocate args array or reuse one per thread

    for(int i = 0; i < N_TOTAL; ++i){
        atomic_fetch_add(&g_created, 1);
        die_pthread(pthread_create(&ths[i], NULL, flat_worker, NULL), "pthread_create A");
        if ((i + 1) % 1000 == 0) printf("Created threads: %d-%d\n", i - 998, i + 1);
    }

    // TODO: loop i = 0..N_TOTAL-1
    //   - atomic_fetch_add(&g_created, 1)
    //   - pthread_create(&ths[i], NULL, flat_worker, argptr)
    //   - handle rc with die_pthread

    for(int i = 0; i < N_TOTAL; ++i){
       die_pthread(pthread_join(ths[i], NULL), "pthread_join A");
       if ((i + 1) % 1000 == 0) printf("Joined threads: %d-%d\n", i - 998, i + 1);
    }

    free(ths);
    long long end = now_ns();
    print_summary("2.a", start, end);
    return end - start;
}

// ============================================================
// 2.a — Flat (batched)
// ============================================================
static void run2a_flat_batched(int batch_size) {
    printf("\n=== 2.a Flat (BATCHED), batch_size=%d ===\n", batch_size);
    long long start = now_ns();

    // TODO: create N_TOTAL threads in batches:
    // next = 0
    // while next < N_TOTAL:
    //   - batch_count = min(batch_size, N_TOTAL - next)
    //   - allocate pthread_t batch[batch_count] (heap or VLA if allowed)
    //   - create batch_count threads, start them
    //   - join the batch
    //   - next += batch_count
    // end while

    long long end = now_ns();
    print_summary("2.a(batched)", start, end);

    // TODO: verify created == destroyed == N_TOTAL
}

// ============================================================
// 2.b — Two-level hierarchy (parent -> children)
// ============================================================
typedef struct {
    int parent_id;
    // TODO: optional fields for sparse printing
} parent_arg_t;

static void *child_worker_2b(void *arg) {
    (void)arg;
    // TODO: minimal work
    atomic_fetch_add(&g_destroyed, 1);
    return NULL;
}

static void *parent_worker_2b_no_batching(void *arg) {
    parent_arg_t *pa = (parent_arg_t *)arg;
    //pthread *children = malloc(sizeof(*children) * B_CHILDREN_PER_PARENT);
    int pid = pa->parent_id;
    printf("Parent %d started\n", pid);
    
    pthread_t children[B_CHILDREN_PER_PARENT];

    // TODO: create B_CHILDREN_PER_PARENT child threads
    //   - allocate pthread_t children[B_CHILDREN_PER_PARENT]
    //   - loop child_id: atomic_fetch_add(&g_created, 1); pthread_create(...)
    // TODO: join all children
    // TODO: free pa if heap-allocated

    // Parent creates children.
    for (int i = 0; i < B_CHILDREN_PER_PARENT; ++i) {
        atomic_fetch_add(&g_created, 1);
        die_pthread(pthread_create(&children[i], NULL, child_worker_2b, NULL), "pthread_create B child");
        if ((i + 1) % 25 == 0) {
            printf("Parent %d created children: %d-%d ... %d-%d\n", pid, pid, i - 23, pid, i + 1);
        }
    }

    // Parent joins children.
    for (int i = B_CHILDREN_PER_PARENT - 1; i >= 0; --i) {
        die_pthread(pthread_join(children[i], NULL), "pthread_join B child");
    }
    printf("Parent %d joined children: %d-%d ... %d-1\n", pid, pid, B_CHILDREN_PER_PARENT, pid);
    printf("Parent %d completed\n", pid);

    atomic_fetch_add(&g_destroyed, 1); // parent destroyed
    free(pa);
    return NULL;
}

static long long run2b_two_level_no_batching(void) {
    printf("\n=== 2.b Two-level (no batching) ===\n");
    long long start = now_ns();

    // TODO: allocate pthread_t parents[B_PARENTS]
    // TODO: for parent_id in 1..B_PARENTS:
    //   - atomic_fetch_add(&g_created, 1) // parent
    //   - allocate parent_arg_t on heap or static storage
    //   - pthread_create parent thread -> parent_worker_2b_no_batching
    // TODO: join all parents

    pthread_t parents[B_PARENTS];
    // Create the 50 parents
    for (int i = 0; i < B_PARENTS; ++i) {
        parent_arg_t *arg = malloc(sizeof(*arg));
        arg->parent_id = i + 1;
        atomic_fetch_add(&g_created, 1);
        die_pthread(pthread_create(&parents[i], NULL, parent_worker_2b_no_batching, arg), "pthread_create B parent");
    }

    for (int i = 0; i < B_PARENTS; ++i) {
        die_pthread(pthread_join(parents[i], NULL), "pthread_join B parent");
    }

    long long end = now_ns();
    print_summary("2.b", start, end);
    return end - start;
}

// ============================================================
// 2.b — Two-level hierarchy (batched children, if needed)
// ============================================================
typedef struct {
    int parent_id;
    int child_batch_size;
} parent_batch_arg_t;

static void *parent_worker_2b_batched(void *arg) {
    parent_batch_arg_t *pa = (parent_batch_arg_t *)arg;

    // TODO: inside each parent:
    // nextChild = 1
    // while nextChild <= B_CHILDREN_PER_PARENT:
    //   - create up to child_batch_size children
    //   - join that batch
    // end while
    // TODO: free pa if heap-allocated

    atomic_fetch_add(&g_destroyed, 1); // parent destroyed
    return NULL;
}

static void run2b_two_level_batched(int child_batch_size) {
    printf("\n=== 2.b Two-level (BATCHED children), child_batch_size=%d ===\n", child_batch_size);
    long long start = now_ns();

    // TODO: same as run2b_two_level_no_batching, but parent uses parent_worker_2b_batched
    // and child_batch_size is passed in via parent_batch_arg_t.

    long long end = now_ns();
    print_summary("2.b(batched)", start, end);

    // TODO: verify created == destroyed == N_TOTAL
}

// ============================================================
// 2.c — Three-level hierarchy (initial -> child -> grandchild)
// ============================================================
typedef struct {
    int initial_id;
} initial_arg_t;

typedef struct {
    int initial_id;
    int child_id;
    int grand_batch_size; // used for batched version
} child_arg_t;

static void *grandchild_worker_2c(void *arg) {
    (void)arg;
    // TODO: minimal work
    atomic_fetch_add(&g_destroyed, 1);
    return NULL;
}

static void *child_worker_2c_no_batching(void *arg) {
    child_arg_t *ca = (child_arg_t *)arg;
    int iid = ca->initial_id;
    int cid = ca->child_id;

    // TODO: create C_GRANDCHILDREN_PER_CHILD grandchild threads
    // TODO: join all grandchildren
    // TODO: free ca if heap-allocated
    
    pthread_t grandkids[C_GRANDCHILDREN_PER_CHILD];

    for (int i = 0; i < C_GRANDCHILDREN_PER_CHILD; ++i) {
        atomic_fetch_add(&g_created, 1);
        die_pthread(pthread_create(&grandkids[i], NULL, grandchild_worker_2c, NULL), "pthread_create C grand");
        if ((i + 1) % 25 == 0) {
            printf("Child %d-%d created grandchildren: %d-%d-%d ... %d-%d-%d\n", iid, cid, iid, cid, i - 23, iid, cid, i + 1);
        }
    }

    for (int i = C_GRANDCHILDREN_PER_CHILD - 1; i >= 0; --i) {
        die_pthread(pthread_join(grandkids[i], NULL), "pthread_join C grand");
    }
    printf("Child %d-%d joined grandchildren: %d-%d-%d ... %d-%d-1\n", iid, cid, iid, cid, C_GRANDCHILDREN_PER_CHILD, iid, cid);
    printf("Child %d-%d completed\n", iid, cid);

    atomic_fetch_add(&g_destroyed, 1); // child destroyed
    free(ca);
    return NULL;
}

static void *initial_worker_2c_no_batching(void *arg) {
    initial_arg_t *ia = (initial_arg_t *)arg;
    int iid = ia->initial_id;
    printf("Initial %d started\n", iid);

    // TODO: create C_CHILDREN_PER_INITIAL child threads
    //   - each child runs child_worker_2c_no_batching
    // TODO: join all children
    // TODO: free ia if heap-allocated

    pthread_t children[C_CHILDREN_PER_INITIAL];

    for (int i = 0; i < C_CHILDREN_PER_INITIAL; ++i) {
        child_arg_t *ca = malloc(sizeof(*ca));
        ca->initial_id = iid;
        ca->child_id = i + 1;
        atomic_fetch_add(&g_created, 1);
        die_pthread(pthread_create(&children[i], NULL, child_worker_2c_no_batching, ca), "pthread_create C child");
        printf("Initial %d created child: %d-%d\n", iid, iid, i + 1);
    }

    for (int i = 0; i < C_CHILDREN_PER_INITIAL; ++i) {
        die_pthread(pthread_join(children[i], NULL), "pthread_join C child");
    }
    printf("Initial %d completed\n", iid);

    atomic_fetch_add(&g_destroyed, 1); // initial destroyed
    free(ia);
    return NULL;
}

static long long run2c_three_level_no_batching(void) {
    printf("\n=== 2.c Three-level (no batching) ===\n");
    long long start = now_ns();

    // TODO: allocate pthread_t initials[C_INITIALS]
    // TODO: for initial_id in 1..C_INITIALS:
    //   - atomic_fetch_add(&g_created, 1) // initial
    //   - allocate initial_arg_t
    //   - pthread_create -> initial_worker_2c_no_batching
    // TODO: join all initials
    //
    
    pthread_t initials[C_INITIALS];
    for (int i = 0; i < C_INITIALS; ++i) {
        initial_arg_t *arg = malloc(sizeof(*arg));
        arg->initial_id = i + 1;
        atomic_fetch_add(&g_created, 1);
        die_pthread(pthread_create(&initials[i], NULL, initial_worker_2c_no_batching, arg), "pthread_create C initial");
    }

    for (int i = 0; i < C_INITIALS; ++i) {
        die_pthread(pthread_join(initials[i], NULL), "pthread_join C initial");
    }

    long long end = now_ns();
    print_summary("2.c", start, end);
    return end - start;
}

// ============================================================
// 2.c — Three-level hierarchy (batched grandchildren, if needed)
// ============================================================
static void *child_worker_2c_batched(void *arg) {
    child_arg_t *ca = (child_arg_t *)arg;

    // TODO: inside each child:
    // nextGrand = 1
    // while nextGrand <= C_GRANDCHILDREN_PER_CHILD:
    //   - create up to ca->grand_batch_size grandchildren
    //   - join that batch
    // end while
    // TODO: free ca if heap-allocated

    atomic_fetch_add(&g_destroyed, 1); // child destroyed
    return NULL;
}

static void *initial_worker_2c_batched(void *arg) {
    initial_arg_t *ia = (initial_arg_t *)arg;

    // TODO: create C_CHILDREN_PER_INITIAL children
    //   - each child runs child_worker_2c_batched with grand_batch_size
    // TODO: join all children
    // TODO: free ia if heap-allocated

    atomic_fetch_add(&g_destroyed, 1); // initial destroyed
    return NULL;
}

static void run2c_three_level_batched(int grand_batch_size) {
    printf("\n=== 2.c Three-level (BATCHED grandchildren), grand_batch_size=%d ===\n", grand_batch_size);
    long long start = now_ns();

    // TODO: same as run2c_three_level_no_batching, but initial uses initial_worker_2c_batched
    // and grand_batch_size is passed down to children via child_arg_t.

    long long end = now_ns();
    print_summary("2.c(batched)", start, end);

    // TODO: verify created == destroyed == N_TOTAL
}

// ============================================================
// main
// ============================================================
int main(void) {
    // TODO: run 3 trials each and compute averages in your report.
    long long elapsedA[3];
    long long elapsedB[3]; 
    long long elapsedC[3];
    for (int i = 0;i<3;i++) {
	printf("Trial %d:\n",i);
        reset_counts();
        elapsedA[i] = run2a_flat_no_batching();
        // reset_counts(); Batching not required as limits are never met.
        // run2a_flat_batched(A_BATCH_SIZE);

        reset_counts();
        elapsedB[i] = run2b_two_level_no_batching();
        // reset_counts();
        // run2b_two_level_batched(B_CHILD_BATCH_SIZE);

        reset_counts();
        elapsedC[i] = run2c_three_level_no_batching();
        // reset_counts();
        // run2c_three_level_batched(C_GRANDCHILD_BATCH_SIZE);
    }
    long long avgA = (elapsedA[0] + elapsedA[1] + elapsedA[2]) / 3;
    long long avgB = (elapsedB[0] + elapsedB[1] + elapsedB[2]) / 3;
    long long avgC = (elapsedC[0] + elapsedC[1] + elapsedC[2]) / 3;
    double avgAms = avgA / 1e6;
    double avgBms = avgB / 1e6;
    double avgCms = avgC / 1e6;
    printf("Averages:\n\n");
    printf("Average 2.a elapsed: %.3f ms\n", avgAms);
    printf("Average 2.b elapsed: %.3f ms\n", avgBms);
    printf("Average 2.c elapsed: %.3f ms\n", avgCms);

    return 0;
}
