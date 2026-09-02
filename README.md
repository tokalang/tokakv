# TokaKV

[![TokaKV package qualification](https://github.com/tokalang/tokakv/actions/workflows/ci.yml/badge.svg)](https://github.com/tokalang/tokakv/actions/workflows/ci.yml)

**A durable embedded key-value engine written in pure Toka. Write data, restart
the process, recover it, and see how ownership keeps snapshots and leased value
views safe.**

TokaKV combines a write-ahead log, MVCC snapshots, immutable SSTables,
snapshot-aware compaction, and an owner-pinned block cache without native
dependencies or garbage collection. It is an official Public Preview package
for the Toka RC10 SDK.

![TokaKV RC10 quickstart: create a project, add TokaKV, write data, and verify recovery](https://raw.githubusercontent.com/tokalang/tokakv/main/demo/tokakv-quickstart.gif)

## Ten-minute tour

### 1. Install Toka RC10

Linux and macOS SDK archives are published for x86_64 and aarch64:

```sh
curl -fsSL https://tokalang.dev/install.sh | bash -s -- v1.0.0-rc.10
toka doctor
```

### 2. Create a project and add TokaKV

```sh
toka new tokakv-tour
cd tokakv-tour
toka add tokakv
```

### 3. Replace `src/main.tk`

```toka
import std/io::{println}
import official/tokakv::{TokaKvEngine}

const DB_PATH = "tokakv-tour-data"
const ACCOUNT_KEY = "account:42"

fn main() -> i32 {
    auto db = TokaKvEngine::open(string::from(DB_PATH)).unwrap()
    auto existing = db#.get(string::from(ACCOUNT_KEY)).unwrap()

    if existing.is_none() {
        println("[TokaKV] FIRST RUN")
        db#.put(string::from(ACCOUNT_KEY), string::from("100")).unwrap()
        println("write: {} = 100", ACCOUNT_KEY)

        {
            auto snapshot = db#.acquire_snapshot().unwrap()
            db#.put(string::from(ACCOUNT_KEY), string::from("125")).unwrap()

            auto old_value = db#
                .get_at_snapshot(string::from(ACCOUNT_KEY), snapshot)
                .unwrap()
                .unwrap()
            auto latest_value = db#.get(string::from(ACCOUNT_KEY)).unwrap().unwrap()
            println("snapshot: {} = {}", ACCOUNT_KEY, old_value)
            println("latest:   {} = {}", ACCOUNT_KEY, latest_value)
            assert(old_value.as_str().equals("100"), "snapshot must retain the old value")
            assert(latest_value.as_str().equals("125"), "latest read must see the update")
        }

        auto leased = db#
            .get_lease(string::from(ACCOUNT_KEY))
            .unwrap()
            .into_value()
            .unwrap()
        assert(leased.as_str().equals("125"), "leased read must see the latest value")
        db#.close().unwrap()
        println("lease after close: {}", leased.as_str())
        println("NEXT: run `toka run` again to verify WAL recovery")
        return 0
    }

    auto recovered = existing.unwrap()
    println("[TokaKV] SECOND RUN")
    println("recovered: {} = {}", ACCOUNT_KEY, recovered)
    println("sequence: {}", db#.current_seq())
    assert(recovered.as_str().equals("125"), "reopened database must recover the latest value")
    assert(db#.current_seq() == 2:u64, "WAL replay must recover both committed writes")
    db#.close().unwrap()
    println("RECOVERY VERIFIED")
    return 0
}
```

The checked-in [tour source](https://github.com/tokalang/tokakv/blob/main/examples/ten-minute-tour/src/main.tk) adds explicit
assertions to every claim made by this compact README version.

### 4. Run it twice

```sh
toka run
toka run
```

The first process writes two versions, reads both the snapshot and latest
value, and proves that an outstanding value lease remains valid after the
engine closes:

```text
[TokaKV] FIRST RUN
snapshot: account:42 = 100
latest:   account:42 = 125
lease after close: 125
NEXT: run `toka run` again to verify WAL recovery
```

The second process reopens the same directory. Because `close()` does not flush
the active MemTable, this path specifically verifies replay from the durable
write-ahead log:

```text
[TokaKV] SECOND RUN
recovered: account:42 = 125
sequence: 2
RECOVERY VERIFIED
```

RC10 can print known `W0408` warnings from its SDK build modules to stderr.
They do not invalidate a successful build or the markers above. The repository
keeps the full diagnostics visible instead of hiding them in the public guide.

## Why ownership, leases, and snapshots matter

| TokaKV concept | What it protects | What the tour proves |
| :--- | :--- | :--- |
| Ownership | Engine, cache, and storage resources have deterministic owners and cleanup | Closing the engine cannot leave an outstanding leased view dangling |
| `ValueLease` | A decoded value view remains attached to the owner that keeps its backing storage alive | `lease.as_str()` remains valid after cache or engine visibility changes |
| `SnapshotLease` | A point-in-time sequence stays authoritative while the RAII lease is alive | The snapshot reads `100` after the latest value becomes `125` |

Read [Ownership, leases, and snapshots](https://github.com/tokalang/tokakv/blob/main/docs/ownership-lease-snapshot.md) for
the compiler-enforced boundaries, including examples that Toka rejects.

## Public Preview status

- Package identity: `official/tokakv`
- Supported hosts: Linux and macOS on x86_64 and aarch64
- Toka SDK: `v1.0.0-rc.10`
- Native dependencies: none
- Current compaction scope: L0-to-L1
- Non-goals: distributed replication, consensus, Redis protocol serving, and
  asynchronous disk offload

TokaKV is not yet a stable 1.0 database compatibility promise. It is a
qualified embedded engine and a concrete systems-programming demonstration of
Toka's ownership and resource semantics.

## Verify the public quickstart

From a checkout of this repository, point the verifier at a published RC10 SDK:

```sh
TOKA=/path/to/rc10/bin/toka tools/verify_quickstart.sh
```

Maintainers can test an unpublished checkout instead of the registry package:

```sh
TOKA=/path/to/rc10/bin/toka TOKAKV_SOURCE="$PWD" tools/verify_quickstart.sh
```

The verifier creates a clean temporary project, runs `toka add`, executes two
separate processes, and fails unless snapshot, lease, value, and recovery
markers all match.

## Architecture and qualification details

### Phase 1: WAL and durability invariants

1. **Append-Only Write-Ahead Log (WAL)**:
   - 8-byte LE header (`[CRC32: 4B LE][PayloadLen: 4B LE]`) + typed payload (`[Op: 1B][Seq: 8B LE][KeyLen: 4B LE][KeyBytes][ValLen: 4B LE][ValBytes]`).
   - Pure Toka IEEE 802.3 CRC32 bitwise checksum matching standard vector `0xCBF43926`.
   - Explicit length bounds: `MAX_KEY_BYTES = 64KB`, `MAX_VALUE_BYTES = 32MB`, `MAX_RECORD_BYTES = 33.6MB`.

2. **Strict Sequence Monotonicity**:
   - `WalWriter` and `replay_and_recover` enforce strict sequential monotonicity: the first record requires `seq >= 1`, and every subsequent record strictly requires `seq == previous_seq + 1`.
   - Any out-of-order, duplicate, or gapped sequence fails closed with `KvError::corrupted("non_monotonic_sequence")`.

3. **Fail-Closed Crash Recovery & Physical Truncation**:
   - **Torn Tail at EOF**: Incomplete header or incomplete payload at EOF triggers physical `ftruncate` rollback via `WalFile::truncate` + `sync_all` + `close`. Any I/O error during recovery immediately aborts startup.
   - **Corrupted Frame**: Full frame CRC mismatch fails closed with `KvError::corrupted("crc_mismatch")`.
   - **Non-ENOENT Open Errors**: Attempting to open directories or paths with permission errors returns `KvError::io` and fails closed.

4. **Poison Lifecycle on Write/Sync Failure**:
   - Any `write_all_at`, `sync_data`, `truncate`, or `sync_all` failure marks `WalWriter.poisoned = true` and `Engine.poisoned = true`.
   - `next_seq` is never incremented if WAL persistence fails.
   - Subsequent `put`, `delete`, `rotate_memtable`, and `close` fail closed with `KvError::poisoned` (code `-6`). Recovery requires clean restart and replay.

5. **In-Memory MemTable & Rotation**:
   - Single-writer binary search table with exact `size_bytes` calculation upon insertions, overwrites, and tombstone deletes.
   - `freeze(cede self) -> FrozenMemTable` consumes the active table, sealing it into an immutable snapshot without mutable aliasing.

### Phase 2A: SSTable offline closed loop

1. **Immutable SSTable Format (V1)**:
   - **Data Blocks (4KB target)**: Block format `[CRC32: 4B LE][DataLength: 4B LE][Count: 4B LE][Entries...]`. Each entry contains `[Tag: 1B (0=Put, 1=Delete)][Seq: 8B LE][KeyLen: 4B LE][KeyBytes][ValLen: 4B LE][ValBytes]`.
   - **Index Block**: Block format `[CRC32: 4B LE][DataLength: 4B LE][Count: 4B LE][IndexEntries...]`. Each entry contains `[LastKeyLen: 4B LE][LastKeyBytes][BlockOffset: 8B LE][BlockLength: 8B LE]`.
   - **Exact 48-Byte Footer**:
     - `0..7`: `IndexBlockOffset` (`u64 LE`)
     - `8..15`: `IndexBlockLength` (`u64 LE`)
     - `16..23`: `MinSeq` (`u64 LE`)
     - `24..31`: `MaxSeq` (`u64 LE`)
     - `32..39`: ASCII bytes `[0x54, 0x4F, 0x4B, 0x41, 0x53, 0x53, 0x54, 0x31]` (`"TOKASST1"`)
     - `40..43`: `FooterCRC32` (`u32 LE`, IEEE 802.3 over bytes `0..39`)
     - `44..47`: `Reserved` (`u32 LE`, strictly 0)

2. **Durable SSTable Publication (`PendingOutputFile`)**:
   - Atomic temporary file creation with `.tmp_sstable_<pid>_<seq>_XXXXXX` sibling in the exact target parent directory.
   - Atomic no-replace rename (`RENAME_NOREPLACE` on Linux / `link` + `unlink` on Darwin) ensuring published SSTables are never overwritten.
   - Three-stage commit state machine: `PRE_RENAME (0) -> RENAMED_DIR_SYNC_FAILED (1) -> COMMITTED (2)`.
   - Post-rename directory sync failures return `commit_uncertain` while preserving target file on disk (never unlinked).

3. **Fail-Closed Point-Lookup Loop (`SSTableReader`)**:
   - Uses handle-based physical `file.size()` to safely gate all footer, index, and block offsets.
   - Three-tier point lookup semantics: `Result<Option<Option<string> >, KvError>`:
     - `Ok(None)`: Miss
     - `Ok(Some(None))`: Tombstone
     - `Ok(Some(Some(v)))`: Hit with value payload
     - `Err(KvError)`: CRC/Corruption/IO (never downgraded to miss)

### Phase 2B: Manifest and VersionSet integration

1. **Manifest Protocol & Atomic VersionEdit (`TOKAMNF1`)**:
   - 8-byte magic header `"TOKAMNF1"`.
   - Single atomic record `TAG_VERSION_BATCH` merges added tables, watermark `last_persisted_seq`, and `next_file_number`.
   - Durable file number pre-allocation (`TAG_ALLOC_NUM`) prevents number reuse across crashes.
   - Torn tails at EOF are safely truncated, while complete records with corrupted CRC always fail closed.

2. **Durable Container & Directory Hierarchy**:
   - Standard directory-separated layout: `<db_dir>/MANIFEST`, `<db_dir>/wal.log`, `<db_dir>/000001.sst`.
   - Container creation durably syncs parent directory: `sync_directory(parent_of_db_dir)`.
   - First-time `wal.log` creation and `MANIFEST` creation durably sync `db_dir`: `sync_directory(db_dir)`.
   - SSTable publication atomically syncs temp file, renames without replacement, and syncs container directory.

3. **Multi-Version Query Hierarchy & Fail-Closed Engine Queries**:
   - `TokaKvEngine::get(key) -> Result<Option<string>, KvError>` routes through `active_mem -> frozen_mems -> VersionSet`.
   - Key range pruning `[smallest_key, largest_key]` avoids unnecessary disk reads.
   - Any SSTable CRC mismatch or I/O corruption immediately fails closed with `Err(KvError)`, never downgraded to a miss.

### Phase 3A: Safe owner block cache

1. **Safe Owner Lease Lifecycle (`~CachedBlock` / `BlockLease`)**:
   - `BlockLease` owns `~CachedBlock`; `BlockCache` internal map owns `~CachedBlock`.
   - Eviction removes map visibility/ownership without affecting active leases held by reader queries.
   - When all leases and cache entries for a block drop, the block's heap memory is safely reclaimed without raw pointers, `Addr`, or manual refcounts.
   - 100% Safe Toka: Zero `unsafe` blocks, zero raw pointer dereferences in `block_cache.tk`.

2. **Owner-Pinned Value Views (`ValueLease`)**:
   - `TokaKvEngine::get_lease` and `get_lease_at_snapshot` preserve `Hit`, `Deleted`, and `NotFound` as `LeasedLookupResult`.
   - SSTable hits keep `BlockLease + entry_index`, so `ValueLease::as_str() -> str <- self` and `as_bytes() -> bytes <- self` expose decoded cached values without another payload copy.
   - Cache eviction and engine close do not invalidate an outstanding lease; the shared `CachedBlock` is reclaimed only after its final cache/lease owner drops.
   - Active/Frozen MemTable hits use a one-value owned fallback because their read lock cannot safely escape; the existing `get()` copy API remains unchanged.
   - PAL rejects a value view escaping its lease lifetime (`E0455`).

3. **Strict Encapsulation & Field-Level Protection**:
   - `CachedBlock`, `BlockLease`, `BlockCacheInner`, and `BlockCache` are declared `@Encap`.
   - `BlockLease::lookup` performs binary search directly over `CachedBlock` internal entries using safe borrowed access without copying or moving `Vec<Entry>`.
   - Diagnostic compile-fail tests verify private member isolation:
     - `diag_block_cache_private_fields.tk`: Accessing `BlockLease.~block` fails with `E0418`.
     - `diag_block_cache_cannot_mutate_entries.tk`: Accessing `CachedBlock.entries` fails with `E0418`.
     - `diag_block_cache_cannot_mutate_inner.tk`: Accessing `BlockCache.~inner` fails with `E0418`.

4. **Immutable Outer Receiver & Double-Check Loading**:
   - `BlockCache::get_or_load(self, ...)` and `BlockCache::stats(self)` provide immutable `self` receivers backed by internal `Mutex<BlockCacheInner>`.
   - Lock payload access uses safe borrowed references (`auto &inner# = lock.borrow_mut()`).
   - Miss loader performs un-locked disk I/O via path parameter (`sst_path: string`) rather than consuming `@Encap` resource handles.
   - Re-acquires cache mutex upon decoded block construction to perform double-check insertion against concurrent peer workers.

5. **Estimated Resident Memory Accounting & LRU Eviction**:
   - Explicit `estimated_resident_bytes` accounting tracks block length, entry count (32 bytes overhead each), and key/value byte lengths.
   - Least Recently Used (LRU) eviction chain evicts oldest blocks when `resident_bytes + block_size > capacity_bytes`.
   - Blocks exceeding cache capacity bypass insertion and are returned directly as transient leases.
   - Decoded block CRC mismatches and I/O errors are never cached (fail-closed bypass).

6. **Full LLVM IR ThreadSanitizer (TSan) Qualification**:
   - `tokac --emit-llvm` generates complete LLVM IR for the concurrent test suite and library code.
   - `clang -fsanitize=thread` compiles the LLVM IR, instrumenting all Toka generated functions, memory operations, and synchronization points.
   - Jointly linked with `toka_rt_tsan.o` and executed under ThreadSanitizer with 0 data races and 0 concurrency defects.

### Phase 3B: ReadState and WriterState separation

1. **State Decoupling & Concurrency Architecture**:
   - `ReadState`: Immutable/read-only snapshot structures (`active_mem#: MemTable`, `frozen_mems#: Vec<FrozenMemTable>`, `current_version#: Version`, `health#: u8`) implementing `@Send + @Sync` and protected by `RwMutex<ReadState>`.
   - `WriterState`: Single-writer resources (`wal_writer#: WalWriter`, `version_set#: VersionSet`, `next_seq#: u64`, `next_flush_id#: u64`, `opened#: bool`, `poisoned#: bool`, `db_dir: string`) strictly implementing `@Send` only (NEVER `@Sync`). Thread-safe multi-threaded sharing is exclusively provided via `Mutex<WriterState>`.
   - `TokaKvEngine`: Encapsulated facade holding `~reader: RwMutex<ReadState>`, `~writer: Mutex<WriterState>`, `block_cache: BlockCache`, implementing `@Send + @Sync` and `@Encap`.

2. **Strict Global Lock Hierarchy**:
   - **Writer Path**: `Writer Mutex -> Reader Write Lock -> BlockCache Mutex`
   - **Reader Path**: `Reader Read Lock -> BlockCache Mutex`
   - Strictly acyclic: Reader locks never acquire writer locks; reverse lock ordering is strictly prohibited across the entire codebase.

3. **Fail-Closed Health Gating on Readers**:
   - `ReadState` maintains `health#: u8` (`HEALTH_READY = 0`, `HEALTH_POISONED = 1`, `HEALTH_CLOSED = 2`).
   - `TokaKvEngine::get(self, key)` runs concurrently across readers under `RwReadLock<ReadState>` with **zero contention on the writer mutex**.
   - Any durability, WAL write, or Manifest commit failure marks `ReadState.health = HEALTH_POISONED` under a brief `RwWriteLock<ReadState>`, causing all subsequent reader queries to immediately fail closed with `KvError::poisoned`.

4. **Two-Stage Flush Protocol with Stable Flush IDs**:
   - **Stage 1 (Rotate under brief reader write lock)**: Assigns a monotonic `cur_flush_id`, calls `take_and_freeze(cur_flush_id)` on the active MemTable, and pushes the snapshot to `frozen_mems`. Readers continue querying the snapshot seamlessly with **zero query gap**.
   - **Stage 2 (Disk I/O & Manifest commit unlocked from readers)**: Allocates file number, writes SSTable via sibling atomic temp file, and commits `TAG_VERSION_BATCH` to the `MANIFEST`—all without holding the reader lock.
   - **Stage 3 (Version install & retire under brief reader write lock)**: Installs the new `Version` and retires specifically the `FrozenMemTable` matching `cur_flush_id`.

5. **Diagnostic Compile-Fail & Full LLVM IR TSan Verification**:
   - `diag_engine_private_fields.tk`: Accessing `TokaKvEngine.~reader` fails with `E0418`.
   - `diag_engine_writer_state_private_fields.tk`: Accessing `WriterState.wal_writer` fails with `E0418`.
   - `concurrent_engine_read_write_v1.tk`: 4 reader threads + 2 writer threads running concurrent writes, flushes, and reads under full LLVM IR ThreadSanitizer instrumentation (0 races, 0 errors).

## Known Boundaries, Technical Debt & Future Roadmap

- **Tail Corruption Tolerance Strategy**: Incomplete frame headers or incomplete payloads at EOF are treated as torn tails and physically truncated; complete frames with invalid CRC unconditionally fail closed.
- **Pinned-After-Eviction Accounting**: `CacheStats.estimated_resident_bytes` counts blocks still resident in the LRU map; an evicted block retained solely by an outstanding `ValueLease` remains memory-safe but is not included in that counter.
- **Current Leveled Scope**: Compaction currently targets L0-to-L1; deeper levels, distributed replication, and the Redis protocol server remain future work.
