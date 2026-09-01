# TokaKV v0.1.2 release notes

**Status:** Prepared for qualification and publication. No tag or immutable
GitHub Release exists until the maintainer authorizes publication.

TokaKV `v0.1.2` is the RC10 product-onboarding release. It does not change the
qualified storage engine implementation or public API from `v0.1.1`; it aligns
the package metadata with Toka `v1.0.0-rc.10` and adds a verified path for a new
developer to install, write, read, restart, recover, and understand the engine's
ownership model.

## User-facing additions

- Product-oriented README with the ten-minute tour before architecture detail.
- Two-process example that proves snapshot isolation, owner-pinned leased reads,
  and write-ahead-log recovery.
- Dedicated ownership, `ValueLease`, and `SnapshotLease` guide with a
  compiler-rejected escaping-view example.
- `tools/verify_quickstart.sh`, which creates a clean RC10 project and checks
  both process runs and every documented result marker.
- Reproducible VHS cassette plus generated GIF and WebM terminal recordings.

## Compatibility and scope

- Required compiler metadata: `1.0.0-rc.10`
- Package identity: `official/tokakv`
- Native dependencies: none
- Supported hosts: Linux and macOS, x86_64 and aarch64
- Storage implementation and API: unchanged from `v0.1.1`
- Current compaction boundary: L0-to-L1

## Publication gates

Before creating `v0.1.2`, all of the following must pass from a clean source
state:

1. `TOKA_SDK=/path/to/rc10 TOKA_EXPECT_VERSION=1.0.0-rc.10 python3 tests/qualify_package.py`
2. Local-path quickstart replay with the published RC10 SDK
3. Deterministic package archive generation and two-build digest comparison
4. Archive-only quickstart replay
5. Maintainer review of the generated GIF/WebM and release notes
6. Explicit maintainer authorization for the immutable tag and GitHub Release

The reproducible release gate is:

```sh
python3 tools/qualify_release.py --sdk /path/to/extracted/rc10 \
  --output /tmp/tokakv-0.1.2.tar.gz
```

After publication, the registry entry must use the exact GitHub Release archive
URL and SHA-256, then the bare `toka add tokakv` quickstart must pass again from
a clean temporary project.
