// jsdom does not implement IndexedDB. idb-keyval (used by the offline write
// queue and the TanStack Query IDB persister) needs a real-enough IDB impl
// to run under Vitest, so we polyfill it globally before any test module
// that touches idb-keyval is imported.
import "fake-indexeddb/auto";
