import { createStore } from "idb-keyval";
import { beforeEach, describe, expect, it } from "vitest";

import { createOfflineQueue, type SupabaseLike } from "./queue";

/**
 * Records every call made against the fake client as a string like
 * `insert:manual_payments:a`, so assertions can check both *what* ran and
 * *in what order* — the property this suite is actually testing.
 */
function createMockSupabase(callLog: string[], failOn?: string): SupabaseLike {
  return {
    from(table) {
      return {
        async insert(payload) {
          const id = (payload as { id?: string }).id ?? "unknown";
          if (failOn && id === failOn) {
            return { error: { message: `simulated failure for ${id}` } };
          }
          callLog.push(`insert:${table}:${id}`);
          return { error: null };
        },
        update(payload) {
          return {
            async match(match) {
              callLog.push(`update:${table}:${JSON.stringify(payload)}:${JSON.stringify(match)}`);
              return { error: null };
            },
          };
        },
        delete() {
          return {
            async match(match) {
              callLog.push(`delete:${table}:${JSON.stringify(match)}`);
              return { error: null };
            },
          };
        },
      };
    },
  };
}

// Each test gets its own idb-keyval store (unique DB name) so queued state
// from one test can never leak into another.
let storeCounter = 0;
function freshStore() {
  storeCounter += 1;
  return createStore(`offline-queue-test-${storeCounter}`, "mutations");
}

describe("offline write queue", () => {
  beforeEach(() => {
    Object.defineProperty(window.navigator, "onLine", { value: true, configurable: true });
  });

  it("flushes enqueued mutations to Supabase in FIFO (enqueue) order", async () => {
    const callLog: string[] = [];
    const queue = createOfflineQueue({ store: freshStore(), client: createMockSupabase(callLog) });

    await queue.enqueue({ table: "manual_payments", operation: "insert", payload: { id: "a" } });
    await queue.enqueue({ table: "manual_payments", operation: "insert", payload: { id: "b" } });
    await queue.enqueue({ table: "manual_payments", operation: "insert", payload: { id: "c" } });

    expect(await queue.pendingCount()).toBe(3);

    const result = await queue.flush();

    expect(callLog).toEqual([
      "insert:manual_payments:a",
      "insert:manual_payments:b",
      "insert:manual_payments:c",
    ]);
    expect(result.flushed).toHaveLength(3);
    expect(result.remaining).toBe(0);
    expect(await queue.pendingCount()).toBe(0);
  });

  it("stops at the first failure and preserves the remaining order for the next retry", async () => {
    const callLog: string[] = [];
    const queue = createOfflineQueue({ store: freshStore(), client: createMockSupabase(callLog, "b") });

    await queue.enqueue({ table: "manual_payments", operation: "insert", payload: { id: "a" } });
    await queue.enqueue({ table: "manual_payments", operation: "insert", payload: { id: "b" } });
    await queue.enqueue({ table: "manual_payments", operation: "insert", payload: { id: "c" } });

    const result = await queue.flush();

    // "a" landed, "b" failed, "c" was never attempted — ordering preserved.
    expect(callLog).toEqual(["insert:manual_payments:a"]);
    expect(result.flushed).toHaveLength(1);
    expect(result.remaining).toBe(2);

    const remaining = await queue.readQueue();
    expect(remaining.map((m) => (m.payload as { id: string }).id)).toEqual(["b", "c"]);

    // A subsequent successful flush (e.g. once the network recovers)
    // resumes from "b", never re-sending "a".
    const secondResult = await queue.flush();
    expect(callLog).toEqual([
      "insert:manual_payments:a",
      "insert:manual_payments:b",
      "insert:manual_payments:c",
    ]);
    expect(secondResult.remaining).toBe(0);
  });

  it("does not attempt to flush while the browser reports offline", async () => {
    Object.defineProperty(window.navigator, "onLine", { value: false, configurable: true });
    const callLog: string[] = [];
    const queue = createOfflineQueue({ store: freshStore(), client: createMockSupabase(callLog) });

    await queue.enqueue({ table: "manual_payments", operation: "insert", payload: { id: "a" } });
    const result = await queue.flush();

    expect(callLog).toEqual([]);
    expect(result.remaining).toBe(1);
  });

  it("notifies subscribers of the pending count as mutations are enqueued and flushed", async () => {
    const callLog: string[] = [];
    const queue = createOfflineQueue({ store: freshStore(), client: createMockSupabase(callLog) });
    const seen: number[] = [];
    const unsubscribe = queue.subscribe((count) => seen.push(count));

    await queue.enqueue({ table: "manual_payments", operation: "insert", payload: { id: "a" } });
    await queue.enqueue({ table: "manual_payments", operation: "insert", payload: { id: "b" } });
    await queue.flush();

    expect(seen).toEqual([1, 2, 0]);
    unsubscribe();
  });
});
