# Week 3 independent-agent dogfood

**Date:** 2026-09-01  
**Scope:** Toka `v1.0.0-rc.10`, public `official/tokakv` `v0.1.2`, and the
published ten-minute tour.  
**Result:** Functional/product goals passed; the Week 3 release-quality gate
did **not** pass because P1 onboarding/tooling defects remain.

## Evidence boundary

These are ten independent AI-agent trials, not ten human interviews. Each agent
received a target-user persona, a unique disposable environment, and the same
black-box protocol. Agents were prohibited from reading the local Toka/TokaKV
source or tests, viewing another trial, delegating, or asking the maintainer for
help. They used only public RC10 artifacts, `tokalang.dev`, public GitHub, and
the public registry.

This is useful reproducible dogfood evidence, but it must not be presented as a
substitute for future human usability research. Environment coverage was eight
macOS arm64 trials, one clean Ubuntu x64 trial, and one clean Ubuntu arm64
trial.

## Protocol

Each trial independently had to:

1. install and verify RC10;
2. create a project and run `toka add tokakv`;
3. run the public tour twice and confirm WAL recovery;
4. modify the program with delete, snapshot, or lease behavior;
5. deliberately create an ownership error, interpret it, and repair it;
6. record timing, exact blockers, source-build need, willingness, and any
   compiler crash, double-drop symptom, or hang.

No trial received live guidance. Independent troubleshooting was capped at 30
minutes.

## Trial results

Times are wall-clock milestones reported by the independent agent. `≤ total`
means the agent timed the whole session reliably but did not split that
particular milestone precisely; no finer value is invented here.

| ID | Persona | Environment | Install/doctor ready | First successful app | Tour complete | Independent modification | Ownership diagnostic | Continue? | Outcome |
| :--- | :--- | :--- | ---: | ---: | ---: | :--- | :--- | :---: | :--- |
| 01 | Rust systems developer | macOS arm64 | 4m14s | 8m49s | 8m59s | delete / tombstone / write-back | `E0455`, independently fixed | 7/10 | Pass with workarounds |
| 02 | Zig systems developer | macOS arm64 | 4m06s | 6m20s | 6m22s | additional snapshot (`v1`/`v2`) | `E0438`, independently fixed | 7/10 | Pass |
| 03 | C++ infrastructure engineer | Ubuntu x64 | about 8m27s incl. prerequisites | about 9m11s | about 9m15s | owner-pinned lease after close | `E0455`, independently fixed | 7/10 | Pass with Linux prerequisites |
| 04 | Storage-engine engineer | macOS arm64 | 1m24s | 3m12s | 3m20s | delete + snapshot + tombstone recovery | `E0455`, independently fixed | 7/10 | Pass |
| 05 | Database/SQL engineer | macOS arm64 | 35s | 1m56s | about 1m58s | delete + snapshot isolation | `E04640`, independently fixed | 7/10 | Pass |
| 06 | Linux infrastructure engineer | Ubuntu arm64 | 5m22s incl. prerequisites | 8m03s | 8m09s | idempotent put/delete recovery | `E0455`, independently fixed | 7/10 | Pass with Linux prerequisites |
| 07 | PL/type-systems researcher | macOS arm64 | about 1m10s | ≤6m34s | ≤6m34s | snapshot drop + lease latest value | `E0455`, independently fixed | 8/10 | Pass |
| 08 | AI coding/tooling developer | macOS arm64 | about 42s | ≤6m59s | ≤6m59s | snapshot of WAL-recovered state | `E0455` text/JSON/evidence, independently fixed | 8/10 | Pass |
| 09 | Cross-platform systems maintainer | macOS arm64 | not separately timed | ≤5m42s | ≤5m42s | delete marker and restart recovery | `E0438`, independently fixed | 7/10 | Pass with workaround |
| 10 | Skeptical Rust/storage engineer | macOS arm64 | 2m24s | 3m55s | 4m44s | delete + snapshot + recovery audit | `E0455`, independently fixed | 6/10 | Pass with friction |

## Acceptance scorecard

| Week 3 criterion | Evidence | Result |
| :--- | :--- | :---: |
| At least 8/10 install successfully | 10/10 eventually installed and verified RC10 | Pass |
| At least 6/10 finish within 15 minutes | 10/10 completed the tour within 15 minutes | Pass |
| At least 3 substantive feedback items | 30 ranked feedback items; four consolidated public issues | Pass |
| At least 2 independently modify the example | 10/10 modified and ran new behavior | Pass |
| 0 P0/P1 | 0 P0, but repeated P1 onboarding/tooling blockers | **Fail** |
| 0 issues requiring oral maintainer guidance | 10/10 independently found a workaround and repaired ownership errors | Pass |

Additional outcomes:

- 10/10 independently repaired the intentional ownership diagnostic.
- 10/10 were willing to continue a bounded small project; mean willingness was
  7.1/10.
- 0 compiler crashes, 0 native runtime crashes, 0 observed double-drops, and 0
  hangs/deadlocks.
- 0/10 required a Toka or TokaKV source build.
- The skeptical storage trial confirmed that the second process recovered from
  a WAL while no SSTable existed; it did not accept output text alone as proof.

## Repeated findings

### P1: doctor can report a false-ready SDK

Six macOS/isolated-path trials selected Python 3.9 or no suitable Python and
then failed inside the SDK's Python helper even though doctor had reported
ready. Clean Linux trials also required Clang/LLD and `libssl-dev`; doctor found
the missing linker but did not find missing Python or OpenSSL link inputs.

Typical post-doctor failure:

```text
def package_helper_path() -> Path | None:
TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'
```

or:

```text
/usr/bin/ld: cannot find -lssl
/usr/bin/ld: cannot find -lcrypto
```

Tracking: [tokalang/toka#40](https://github.com/tokalang/toka/issues/40)

### P1: semantic commands are not project-aware

Five trials attempted direct semantic checks. After a successful public package
install, `toka check/evidence src/main.tk` could not resolve
`official/tokakv`; users had to guess package expansion paths or route the file
through a full project build. The AI-tooling trial also received 479 evidence
records for a six-line error once imports were repaired.

Tracking: [tokalang/toka#38](https://github.com/tokalang/toka/issues/38)

### P2: SDK warning output hides user diagnostics

All 10 trials reported roughly 30 repeated `W0408` diagnostics originating in
RC10's `lib/build.tk`, including clean incremental runs. The warning flood
pushed linker and ownership errors away from the first screen.

Tracking: [tokalang/toka#41](https://github.com/tokalang/toka/issues/41)

### P2: package CLI discovery and error propagation

Trials independently observed that `add <url>` does not describe the registry
name path, `toka add --help` is treated as a package name, resolver root causes
can collapse into a generic failure, relocatable archive helper discovery may
depend on explicit `TOKA_LIB`, and successful add does not print the resolved
version/digest.

Tracking: [tokalang/toka#39](https://github.com/tokalang/toka/issues/39)

## Diagnostic quality

The most common deliberate failure was `E0455`: returning a `str` view borrowed
from a local `ValueLease`. Agents consistently understood the owner/view
relationship from the primary span and the `escaping local declared here`
related location. Other independently repaired errors were `E0438` (use after
move) and `E04640` (explicit `cede` supplied to a borrowed parameter).

Human-readable diagnostics were sufficient for 10/10 repairs. JSON diagnostics
provided stable codes, ranges, and related locations. The main remaining
diagnostic ergonomics requests were scoped evidence and optional repair
strategies such as returning an owned copy or returning the owner.

## Fix order

The evidence supports the planned order and does not justify a language semantic
change:

1. installation/environment: doctor Python/OpenSSL checks and documented Linux
   runtime prerequisites;
2. error reporting: propagate package-helper failures and remove SDK warning
   noise;
3. documentation: relocatable archive setup and a delete/tombstone extension;
4. API/tooling ergonomics: project-aware check/evidence and scoped evidence;
5. language semantics: no change indicated by these trials.

## Remediation status

The two P1 classes found by this trial have been addressed on the development
line without changing language semantics:

- [tokalang/toka#42](https://github.com/tokalang/toka/pull/42) makes `toka
  doctor` execute the packaged Python helper, checks Linux OpenSSL linker
  inputs, and makes `check` and semantic commands project-aware on the
  published macOS/Linux SDK targets. Installed-SDK regression coverage passed
  Linux x64, Linux arm64, macOS arm64, and the existing Windows/MSYS2 dogfood
  path.
- [tokalang/toka-web#2](https://github.com/tokalang/toka-web/pull/2) is deployed
  and documents current-shell activation plus the complete Ubuntu/Debian
  prerequisites in both languages and in the TokaKV tour.
- [tokalang/toka#40](https://github.com/tokalang/toka/issues/40) is closed. The
  project-resolution portion of [tokalang/toka#38](https://github.com/tokalang/toka/issues/38)
  is fixed; scoped evidence volume remains open as a P2.

RC10 is an immutable published artifact, so its embedded CLI has not changed.
The CLI remediations will reach users in the next SDK candidate; the public
documentation mitigations apply to RC10 immediately. A replay against that
next candidate is still required before changing the Week 3 release-quality
gate to accepted.

## Decision

The product path is independently reproducible and comfortably meets the
installation, timing, modification, diagnosis, and stability thresholds.
The P1 defects are fixed on `main`, but Week 3 remains **not accepted for
RC10**. The same black-box profiles must be replayed against the next published
SDK candidate before the release-quality gate can change to accepted.

## RC11 same-protocol replay

**Replay date:** 2026-09-02

**Candidate:** Toka `v1.0.0-rc.11`, TokaKV `0.1.2`

**Evidence boundary:** ten new independent AI-agent black-box contexts, not
human interviews. The same public-only, no-guidance, no-source-read boundary
was retained.

RC11 added negative readiness checks to the original protocol. Every trial had
to prove that an unavailable Python runtime made `toka doctor` fail, that the
restored runtime made it pass, that Registry-backed `check --json` and
`evidence --json` worked without guessed package paths, that evidence stdout
was valid JSON, and that SDK-owned `W0408` disappeared while a deliberate
user-source `W0408` remained visible.

| ID | Persona | Environment | Total wall time | Tutorial + WAL after SDK readiness | Independent extension | Ownership repair | RC11 regression checks | Outcome |
| :--- | :--- | :--- | ---: | :---: | :--- | :--- | :---: | :--- |
| 01 | Rust systems developer | macOS arm64 | 10m22s | Pass under 15m | delete + snapshot + lease | `E0455` | Pass | Pass |
| 02 | Zig / low-level developer | macOS arm64 | 11m02s | Pass under 15m | delete + snapshot + lease | `E0438` | Pass | Pass |
| 03 | C++ infrastructure engineer | Ubuntu x64 | 22m45s incl. container prerequisites | Pass under 15m | delete + snapshot + lease | `E0455` | Pass | Pass |
| 04 | Storage-engine engineer | macOS arm64 | 11m59s | Pass under 15m | delete + snapshot + lease + flush/reopen | `E0455` | Pass | Pass |
| 05 | Database / SQL engineer | macOS arm64 | 7m57s | Pass under 15m | delete + snapshot + lease | `E0455` | Pass | Pass |
| 06 | Linux infrastructure engineer | Ubuntu arm64 | 17m47s incl. prerequisites | Pass under 15m | delete + snapshot + lease | `E0455` | Pass | Pass |
| 07 | PL / type-systems researcher | macOS arm64 | about 10m | Pass under 15m | delete + snapshot + lease | `E0455` | Pass | Pass |
| 08 | AI coding/tooling developer | macOS arm64 | 10m05s | Pass under 15m | delete + snapshot + lease | `E0455` | Pass | Pass |
| 09 | Cross-platform systems maintainer | macOS arm64 | about 11m | Pass under 15m | delete + snapshot + lease | `E0438` | Pass, plus relocation failure | **P1 found** |
| 10 | Skeptical Rust/storage engineer | macOS arm64 | 11m24s | Pass under 15m | delete + snapshot + lease + WAL audit | `E0455` | Pass, plus relocation failure | **P1 confirmed** |

### RC11 scorecard

| Criterion | RC11 evidence | Result |
| :--- | :--- | :---: |
| 10/10 install the published SDK | All archives verified and installed; Linux trials covered x64 and arm64 | Pass |
| 10/10 complete tutorial and WAL recovery within 15 minutes after readiness | 10/10; Linux total wall time also included clean prerequisite installation | Pass |
| 10/10 independently modify the example | 10/10 completed delete, snapshot, or lease behavior | Pass |
| 10/10 understand and repair an ownership error | 10/10 repaired `E0455` or `E0438` without guidance | Pass |
| Doctor fails closed for missing runtime inputs | 10/10 negative Python checks; Linux also staged OpenSSL/linker absence | Pass |
| Registry project `check/evidence` works directly | 10/10 valid project-aware JSON | Pass |
| SDK warning cleanup preserves user diagnostics | 10/10 saw zero SDK `W0408` and retained user `W0408` | Pass |
| 0 crash, observed double-drop, or hang | 0/10 observed any of these symptoms | Pass |
| 0 source builds | 0/10 required one | Pass |
| 0 P0/P1 | 0 P0; the same relocatable-SDK P1 occurred independently in 2/10 | **Fail** |

All ten agents were willing to continue a bounded preview project. Reported
scores, when numeric, ranged from 7/10 to 9/10.

### RC11 P1: PATH invocation breaks relocated SDK discovery

Two independent trials moved the complete published SDK tree, unset
`TOKA_LIB`, placed only its `bin` directory on `PATH`, and invoked `toka` by
name. `doctor` and project execution did not share one reliable SDK root;
`build/run` could exit 1 without output. Explicitly setting `TOKA_LIB` to the
same sibling `lib` directory made the project run.

The root cause was `argv[0]`-relative discovery: normal PATH execution keeps
`argv[0]` as `toka`, so sibling tools and libraries were searched relative to
the project directory. Absolute-path tests had hidden the defect.

Tracking: [tokalang/toka#43](https://github.com/tokalang/toka/issues/43)

The fix is on `main` at `5e67f14e`: resolve the manager executable through
`PATH` before deriving sibling paths, emit actionable package-helper failures,
and exercise a moved release-layout SDK by PATH name with `TOKA_LIB` unset in
the ordinary developer-experience suite. This does not change language
semantics or the `0.9.9-16` compiler-interface key. RC11 itself remains
immutable and still contains the defect.

### Repeated non-blocking RC11 findings

- Semantic evidence remains valid but overly broad: roughly 550–606 KB and
  1,589 records for the tutorial, with only six user-source records in the
  AI-tooling trial. Tracking: [#38](https://github.com/tokalang/toka/issues/38).
- `toka run <file>` does not consume the current project lock graph even though
  `check/evidence <file>` do. Tracking: [#46](https://github.com/tokalang/toka/issues/46).
- The canonical tutorial's `auto db#` produces a contradictory `W0401` during
  direct semantic checks. Tracking: [#45](https://github.com/tokalang/toka/issues/45).
- The installer does not yet verify the downloaded archive against the
  published `SHA256SUMS`. Tracking: [#44](https://github.com/tokalang/toka/issues/44).
- Python 3.9 is rejected correctly, but its parser traceback can precede the
  friendly doctor summary; successful `toka add` still leaves resolved version
  and checksum details in `package.lock` rather than the success message.

### RC11 decision

RC11 proves that the original false-ready, project-aware semantic-command, and
SDK-warning failures are fixed. The agentic systems-programming product path
again passed every functional, timing, modification, diagnosis, and stability
criterion.

The Week 3 release-quality gate nevertheless remains **not accepted for
RC11**, because 2/10 independently found the relocatable-SDK P1. RC10 must not
be marked superseded on the strength of this replay. The next candidate should
contain only the `main` DX fix and must replay the same relocation probe before
the gate can close.
