# Ownership, leases, and snapshots in TokaKV

TokaKV uses Toka's type system to make storage lifetimes explicit without
exposing manual reference counting or user-written lifetime parameters. Three
resource types carry most of the public model:

```text
TokaKvEngine
  ├─ SnapshotLease pins an authoritative MVCC sequence
  └─ ValueLease owns or pins the storage behind a decoded value
       └─ str / bytes views borrow from that ValueLease
```

## Ownership: one resource model across memory and disk

`TokaKvEngine` encapsulates its writer, reader, manifest, WAL, background
maintenance, and block-cache state. Callers receive a safe engine facade rather
than handles to those internals. Closing or dropping the facade deterministically
finishes its resources; callers cannot forge an internal writer or cache owner.

The quickstart keeps a `ValueLease` alive while closing the engine:

```toka
auto leased = db
    .get_lease(string::from("account:42"))
    .unwrap()
    .into_value()
    .unwrap()

db.close().unwrap()
println("{}", leased.as_str())
```

The view remains safe because the lease, not ambient engine visibility, owns or
pins what the view needs. Reclamation occurs only after the final relevant
owner drops.

## `ValueLease`: a view cannot outlive its owner

`get()` returns an owned `string`. Use it when a copy is the simplest API.
`get_lease()` returns `LeasedLookupResult`, preserving `Hit`, `Deleted`, and
`NotFound` while allowing a hit to retain its backing value without another
payload copy.

| API | Result shape | Best fit |
| :--- | :--- | :--- |
| `get(key)` | `Result<Option<string>, KvError>` | Simple owned reads |
| `get_lease(key)` | `Result<LeasedLookupResult, KvError>` | Owner-pinned string or byte views |
| `get_at_snapshot(key, snapshot)` | `Result<Option<string>, KvError>` | Owned point-in-time reads |
| `get_lease_at_snapshot(key, snapshot)` | `Result<LeasedLookupResult, KvError>` | Owner-pinned point-in-time views |

Toka's PAL checker rejects returning a borrowed view after its lease dies:

```toka
import official/tokakv/cache/block_cache::{ValueLease}

fn invalid_escape() -> str {
    auto owned = string::from("owned")
    auto lease = ValueLease::from_owned(cede owned)
    return lease.as_str() // rejected: the view would outlive lease
}
```

This is verified by the package's `diag_value_view_outlives_lease.tk`
compile-fail test. It is a compiler boundary, not a convention documented only
in prose.

## `SnapshotLease`: point-in-time reads with RAII cleanup

Acquiring a snapshot records the engine's latest committed sequence. Later
writes can advance the database while reads through the snapshot retain the
older view:

```toka
db.put(string::from("balance"), string::from("100")).unwrap()
auto snapshot = db.acquire_snapshot().unwrap()
db.put(string::from("balance"), string::from("125")).unwrap()

auto old_value = db
    .get_at_snapshot(string::from("balance"), snapshot)
    .unwrap()
    .unwrap()
auto latest = db.get(string::from("balance")).unwrap().unwrap()

assert(old_value.as_str().equals("100"), "snapshot value")
assert(latest.as_str().equals("125"), "latest value")
```

`SnapshotLease` is encapsulated: external code cannot construct or forge one,
and a lease from one engine fails closed when presented to another engine. When
the lease leaves scope, its RAII drop deregisters the sequence so compaction no
longer needs to retain history solely for that snapshot.

## Recovery: the ownership story crosses process boundaries

Every successful `put` or `delete` synchronously appends to the WAL before the
visible in-memory state advances. Reopening the same directory replays valid
records, restores the latest sequence, truncates an incomplete tail, and rejects
a complete but corrupted frame instead of turning corruption into a miss.

The ten-minute tour intentionally closes without flushing the active MemTable.
Its second `toka run` therefore proves WAL recovery rather than merely reopening
an already-written SSTable.

## Current boundary

These contracts do not claim distributed durability or a server protocol.
TokaKV is currently a single-process embedded engine with L0-to-L1 compaction.
Distributed replication, consensus, deeper levels, and asynchronous disk
offload remain outside the Public Preview boundary.
