/**
 * Offline write queue.
 *
 * Mutations made while offline (or while a request simply fails) are
 * appended to an IndexedDB-backed FIFO queue instead of being lost. The
 * queue is flushed to Supabase automatically on reconnect (`online` event)
 * and when the tab regains visibility, and can also be flushed manually
 * (e.g. from a "sync now" button).
 *
 * Ordering guarantee: flush() replays mutations strictly in enqueue order
 * and stops at the first failure, leaving that mutation and everything
 * queued after it in place. This keeps a later retry from ever replaying
 * writes out of sequence (e.g. an `update` reaching Supabase before the
 * `insert` it depends on).
 */
import { createStore, del, get, set, type UseStore } from "idb-keyval";

import { supabase as defaultSupabase } from "../supabase";

export type MutationOperation = "insert" | "update" | "delete";

export type QueuedMutation = {
  id: string;
  table: string;
  operation: MutationOperation;
  payload: Record<string, unknown>;
  /** Row matcher for update/delete, e.g. `{ id: '...' }`. Ignored for insert. */
  match?: Record<string, unknown>;
  createdAt: number;
};

export type PendingListener = (count: number) => void;

/**
 * The subset of the Supabase JS client's query builder this module drives.
 * Kept minimal and structural (not `typeof supabase`) so tests can pass a
 * lightweight fake instead of a real SupabaseClient.
 */
export type SupabaseLike = {
  from: (table: string) => {
    insert: (payload: unknown) => PromiseLike<{ error: { message: string } | null }>;
    update: (payload: unknown) => {
      match: (match: unknown) => PromiseLike<{ error: { message: string } | null }>;
    };
    delete: () => {
      match: (match: unknown) => PromiseLike<{ error: { message: string } | null }>;
    };
  };
};

const QUEUE_KEY = "offline-write-queue:v1";

export type CreateOfflineQueueOptions = {
  /** Custom idb-keyval store, mainly for test isolation. */
  store?: UseStore;
  /** Custom Supabase-like client, mainly for tests. Defaults to the app's real client. */
  client?: SupabaseLike;
};

export function createOfflineQueue(options: CreateOfflineQueueOptions = {}) {
  const store = options.store ?? createStore("{{PRODUCT_SLUG}}-offline-queue", "mutations");
  const client = options.client ?? (defaultSupabase as unknown as SupabaseLike);
  const listeners = new Set<PendingListener>();

  async function readQueue(): Promise<QueuedMutation[]> {
    return (await get<QueuedMutation[]>(QUEUE_KEY, store)) ?? [];
  }

  async function writeQueue(items: QueuedMutation[]): Promise<void> {
    await set(QUEUE_KEY, items, store);
    for (const listener of listeners) listener(items.length);
  }

  function subscribe(listener: PendingListener): () => void {
    listeners.add(listener);
    return () => listeners.delete(listener);
  }

  async function enqueue(mutation: Omit<QueuedMutation, "id" | "createdAt">): Promise<QueuedMutation> {
    const queue = await readQueue();
    const entry: QueuedMutation = {
      ...mutation,
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
      createdAt: Date.now(),
    };
    queue.push(entry);
    await writeQueue(queue);
    return entry;
  }

  async function pendingCount(): Promise<number> {
    return (await readQueue()).length;
  }

  async function clear(): Promise<void> {
    await del(QUEUE_KEY, store);
    for (const listener of listeners) listener(0);
  }

  async function runMutation(mutation: QueuedMutation): Promise<void> {
    const table = client.from(mutation.table);
    if (mutation.operation === "insert") {
      const { error } = await table.insert(mutation.payload);
      if (error) throw error;
      return;
    }
    if (mutation.operation === "update") {
      const { error } = await table.update(mutation.payload).match(mutation.match ?? {});
      if (error) throw error;
      return;
    }
    const { error } = await table.delete().match(mutation.match ?? {});
    if (error) throw error;
  }

  async function flush(): Promise<{ flushed: string[]; remaining: number }> {
    if (typeof navigator !== "undefined" && navigator.onLine === false) {
      return { flushed: [], remaining: (await readQueue()).length };
    }

    const queue = await readQueue();
    const flushed: string[] = [];
    let index = 0;

    // Sequential by design (see module doc): each mutation must land before
    // the next one is attempted, so ordering is never at the mercy of
    // network timing.
    for (; index < queue.length; index += 1) {
      const mutation = queue[index]!;
      try {
        // eslint-disable-next-line no-await-in-loop -- intentional, see comment above
        await runMutation(mutation);
        flushed.push(mutation.id);
      } catch {
        break; // stop at the first failure; leave it + the rest queued for the next retry
      }
    }

    const remaining = queue.slice(index);
    await writeQueue(remaining);
    return { flushed, remaining: remaining.length };
  }

  return { enqueue, flush, pendingCount, clear, subscribe, readQueue };
}

export type OfflineQueue = ReturnType<typeof createOfflineQueue>;

/** Default singleton the app's components/routes import. */
export const offlineQueue: OfflineQueue = createOfflineQueue();

function attachAutoFlush(queue: OfflineQueue): void {
  if (typeof window === "undefined") return;

  const tryFlush = () => {
    void queue.flush();
  };

  window.addEventListener("online", tryFlush);
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") tryFlush();
  });
}

attachAutoFlush(offlineQueue);
