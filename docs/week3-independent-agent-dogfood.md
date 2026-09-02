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

Cross-platform test-launch follow-ups `e253c410` and `d36eeadd` preserve a
basename `argv[0]` while explicitly selecting the relocated executable. The
final ordinary CI passed Linux x64, Linux arm64, macOS arm64, and Windows/MSYS2
([main gate](https://github.com/tokalang/toka/actions/runs/33583805926),
[Windows dogfood](https://github.com/tokalang/toka/actions/runs/33583805940)).
Issue #43 is therefore fixed on `main`, but not retroactively in RC11.

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

## RC12 same-protocol replay

**Replay date:** 2026-09-02

**Candidate:** Toka `v1.0.0-rc.12`, TokaKV `0.1.2`

**Result:** Functional path passed; release-quality gate failed.

RC12 was published as a single-P1 relocation repair candidate. The protocol
retained every RC11 functional check and made a real fresh-shell relocation
probe mandatory: move the complete SDK, remove the old tree, unset
`TOKA_LIB`/`TOKAC`/`TOKA_PATH`, expose only the new `bin` through `PATH`, clear
shell command caches, and invoke `toka` by name rather than by absolute path.

| ID | Persona | Platform | Wall time | Functional protocol | Real PATH relocation | Outcome |
| :--- | :--- | :--- | ---: | :---: | :---: | :--- |
| 01 | Rust systems | macOS arm64 | about 15m | Pass | Pass in ordinary isolated environment | Pass |
| 02 | Zig / low-level | macOS arm64 | 10m16s | Pass | Pass in ordinary isolated environment | Pass |
| 03 | C++ infrastructure | Ubuntu x64 | 13m06s | Pass with explicit-lib workaround | **Fail** | P1 found |
| 04 | Storage engine | macOS arm64 | 12m41s | Pass with workaround | **Fail** | P1 + CodeGen P1 |
| 05 | Database / SQL | macOS arm64 | about 13m | Pass with workaround | **Fail** | P1 found |
| 06 | Linux infrastructure | Ubuntu arm64 | about 18m | Pass with workaround | **Fail** | P1 found |
| 07 | PL / type systems | macOS arm64 | 6m52s | Pass with workaround | **Fail** | P1 found |
| 08 | AI coding/tooling | macOS arm64 | 16m18s | Pass with workaround | **Fail** | P1 + JSON P1 |
| 09 | Cross-platform systems | macOS arm64 | about 12m | Pass with workaround | **Fail** | P1 found |
| 10 | Skeptical Rust/storage | macOS arm64 | 25m37s | Pass with workaround | **Fail** | P1 + JSON P1 |

### RC12 scorecard

- 10/10 verified the published archive and completed the TokaKV/WAL path,
  using an explicit `TOKA_LIB` only after a relocation failure when required.
- 10/10 completed an independent modification and ownership diagnosis/repair.
- 10/10 retained user `W0408` while observing no SDK-owned `W0408`.
- 0 compiler/native crashes, observed double-drops, or uncontrolled hangs.
- 0/10 required a source build for the functional path; several performed an
  additional public-tag source build for provenance evidence.
- **2/10 passed and 8/10 failed the real fresh-shell relocation hard gate.**
- 0 P0; multiple independently reproducible P1 classes remain.

### RC12 P1: the first relocation fix retained a dangling PATH buffer

In the failing profiles, `command -v toka` resolved the relocated binary, but
`doctor` fell back to `/usr/local/lib/toka` and project `run` reported that the
package helper was missing. Absolute-path invocation or an explicit relocated
`TOKA_LIB` succeeded.

The first fix constructed `SplitIterator` from the temporary result of
`path_value.unwrap()`. The iterator retained a raw pointer after that temporary
string was released, so real PATH scanning was undefined and environment
dependent. The prior CI test also selected an explicit executable to preserve a
basename `argv[0]`; it did not exercise ordinary POSIX PATH lookup.

Issue [#43](https://github.com/tokalang/toka/issues/43) was reopened. The
corrected `main` fix at `01c8d953` keeps the PATH string alive and makes
non-Windows tests launch the command through actual PATH lookup.

### Additional RC12 findings

- Successful `capabilities --json` and `cede-obligations --json` emitted full
  LLVM IR before their JSON document. Tracking: [#48](https://github.com/tokalang/toka/issues/48).
- Ordinary source builds from the exact RC12 tag reported `1.0.0-rc.8` because
  the source default was stale. Tracking: [#49](https://github.com/tokalang/toka/issues/49).
- A documented implicit call into a `cede` formal passed `--check-only` but
  failed normal CodeGen with internal `E0761`; explicit caller `cede` worked.
  Tracking: [#50](https://github.com/tokalang/toka/issues/50).
- Evidence scope, tutorial `W0401`, project-aware `run <file>`, installer
  checksum verification, and Python traceback noise remain non-blocking follow-up.

The relocation lifetime, JSON-only, and source-version fixes landed together at
`01c8d953`. The expanded 30-check developer-experience suite passed Linux x64,
Linux arm64, macOS arm64, and Windows/MSYS2
([main gate](https://github.com/tokalang/toka/actions/runs/33600164581),
[Windows dogfood](https://github.com/tokalang/toka/actions/runs/33600164546)).
Issues #43, #48, and #49 are fixed on `main`, not in immutable RC12. Issue #50
remains open.

### RC12 decision

RC12 must not be accepted or used to supersede RC10/RC11. The functional
agentic systems-programming path remains reproducible, but the candidate failed
its only advertised P1 repair in 8/10 independent contexts and exposed two
additional machine-interface/compiler-consistency blockers. The next candidate
must include the corrected real-PATH fix, JSON-only semantic commands, source
version correction, and a resolution for #50 before another tag is created.

## RC13 unpublished-candidate replay

**Replay date:** 2026-09-02

**Exact candidate:** `abea41db0566882486ac58b8ac9764102e456462`, labeled
`v1.0.0-rc.13` only inside unpublished qualification artifacts. No RC13 tag or
GitHub Release existed during this replay.

**Result:** the AI-agent black-box gate passed. Human usability research remains
required before promotion.

The candidate first passed the unified release gate on Linux x64, Linux arm64,
macOS x64, and macOS arm64. The cross-target summary bound all four passing
reports to the exact candidate revision and version label. The manual workflow
uploaded temporary candidate archives without creating a tag or release:
[qualification run](https://github.com/tokalang/toka/actions/runs/33609017378).

Candidate archive SHA-256 values used by the trials:

| Target | SHA-256 |
| :--- | :--- |
| Linux x64 | `d6f2d4c94866921d156672180898a5eb39737f813704977f585e0a72a2d02785` |
| Linux arm64 | `a83b0eeab59571f521426d388d3b4544ae9b798480b6e8f9a1b6dd85f2f7930a` |
| macOS x64 | `734993f350ed93736f0a843d4862f1a1cd7a5f030db1973e45477af74b61ab51` |
| macOS arm64 | `c188e2ae2aa9bb6bede547d3d7f866a30ad8129ec4faac0a87b0e09652cd83df` |

### Evidence boundary

Ten independent agent contexts produced valid RC13 samples. Each used a unique
disposable HOME and trial directory, could not read the local Toka/TokaKV
workspace or another trial, received no live troubleshooting, and used only an
assigned unpublished archive plus the public website, GitHub, and Registry.

One additional macOS x64 attempt ran on an arm64 host through Rosetta with a
mixed-architecture Homebrew environment. It was recorded as environment-blocked
and excluded rather than misrepresented as a native x64 sample. One attempted
agent context was stopped by the execution platform before testing and was also
excluded. Neither appears in the denominator below.

Linux x64 agent samples ran in x86_64/amd64 containers on an arm64 Docker host,
so their functional execution is evidence but their timings are not native x64
performance measurements. Native x64 artifact qualification is supplied by the
GitHub macOS x64 and Linux x64 runners above.

### Trial results

Every valid trial verified the exact archive digest, moved the complete SDK and
removed the old path, started with `env -i`, left `TOKA_LIB`, `TOKAC`, and
`TOKA_PATH` unset, placed only the relocated `bin` plus necessary host tools on
PATH, and subsequently invoked the manager by the command name `toka`.

| ID | Persona | Environment | Total wall time | Relocation + Registry | Tutorial/WAL | Independent extension | Ownership repair | Outcome |
| :--- | :--- | :--- | ---: | :---: | :---: | :--- | :--- | :--- |
| 01 | Rust systems developer | macOS arm64 | 7m00s | Pass | first success 2m36s; repeated recovery | delete + tombstone recovery | independently repaired | Pass |
| 04 | Database engineer | Linux arm64 | 13m23s | Pass | first write + four recoveries | delete + snapshot + lease | `E0455`, independently repaired | Pass |
| 05 | AI coding/tooling developer | macOS arm64 | about 11m | Pass | first write + repeated recovery | delete + snapshot + lease | `E0438`, independently repaired | Pass |
| 06 | Linux infrastructure engineer | Linux x64 container | about 21m incl. prerequisites | Pass | WAL + abort recovery | delete + snapshot + lease | independently repaired | Pass |
| 07 | PL/type-systems researcher | macOS arm64 | about 12m | Pass | WAL + three abrupt-exit recoveries | delete + snapshot + lease | `E0438`, independently repaired | Pass |
| 08 | Storage reliability engineer | macOS arm64 | 8m49s | Pass | WAL + abort recovery | delete + snapshot + lease | `E0455`, independently repaired | Pass |
| 09 | C++/Linux systems developer | Linux x64 container | about 18m incl. prerequisites | Pass | first write + four recoveries | delete + snapshot + lease | `E0455`, independently repaired | Pass |
| 10 | Agentic coding engineer | macOS arm64 | about 9m | Pass | first write + three recoveries | delete + snapshot + lease | `E0455`, independently repaired | Pass |
| 11 | Rust/Linux backend engineer | Linux arm64 | about 10m | Pass, including offline locked run | first write + repeated recovery | delete + snapshot + lease | independently repaired | Pass |
| 12 | Database infrastructure engineer | Linux x64 container | about 16m incl. prerequisites | Pass | first write + three recoveries | delete + snapshot + lease | `E0474`, independently repaired | Pass |

### RC13 scorecard

| Criterion | RC13 evidence | Result |
| :--- | :--- | :---: |
| Exact candidate archive verified | 10/10 matched the assigned SHA-256 | Pass |
| Complete SDK relocation through real PATH name | 10/10; no explicit Toka path variables | Pass |
| Install/readiness path | 10/10 reached a ready SDK after installing documented host prerequisites | Pass |
| Tutorial and WAL recovery within 15 minutes after readiness | 10/10 | Pass |
| Locked project `toka run src/main.tk` | 10/10 resolved Registry TokaKV 0.1.2 | Pass |
| Project-aware JSON | 10/10 produced directly parseable check/evidence JSON; AI-focused trials also parsed capabilities and cede-obligations JSON | Pass |
| Independent example modification | 10/10 completed delete, snapshot, or lease behavior | Pass |
| Ownership diagnosis and repair | 10/10 repaired without maintainer guidance | Pass |
| User W0408 remains visible, SDK W0408 remains absent | 10/10 | Pass |
| Python readiness failure quality | real Python 3.9 trials failed non-silently without traceback; Python 3.10+ passed | Pass |
| Stability | 0 unexpected crashes, observed double-drops, or hangs; repeated and abrupt-exit WAL recovery passed | Pass |
| Toka SDK source build required | 0/10 | Pass |
| P0/P1 | 0 P0, 0 P1 across valid samples | **Pass** |

All ten valid agents were willing to continue a bounded Public Preview project;
reported numeric willingness ranged from 7/10 to 9/10. The result supports the
agentic systems-programming path, not production-database readiness.

### Repeated non-blocking findings

- Semantic evidence remains broad: small TokaKV entry points produced roughly
  147–596 KB and 1,589–1,591 records, mostly from the SDK and dependency. This
  remains the scoped-evidence follow-up in
  [tokalang/toka#38](https://github.com/tokalang/toka/issues/38).
- Several agents found minor CLI ergonomics: generic subcommand help,
  `toka new --help` being interpreted as a project name, no `toka version`
  alias, and an optimized build message whose artifact remains under
  `target/debug`. These are P2/P3 backlog, not reasons to reopen language
  semantics or issue another one-fix RC.
- Python 3.9 is outside the supported Python 3.10+ helper boundary. Real 3.9
  interpreters now fail with one actionable message and no parser traceback;
  simple programs may happen not to exercise the helper, which does not widen
  the supported runtime contract.
- The Registry 0.1.2 package still contains RC10-era README text. The canonical
  GitHub and deployed English/Chinese tutorials were updated during the replay
  to the warning-clean `auto db =` spelling. RC12 installation wording remains
  correct until RC13 is actually promoted.

### RC13 decision

The exact unpublished RC13 candidate closes the three P1 classes exposed by
RC12: real basename/PATH relocation, JSON-only machine commands, and implicit
`cede` check/CodeGen consistency. It also verifies installer checksums,
project-aware `run <file>`, warning-clean starters/tutorials, and clean Python
failure behavior through ordinary release gates.

The Week 3 **AI-agent black-box gate is accepted for the exact candidate
revision**. This does not authorize publication by itself. RC13 remains
untagged and unpublished until 3–5 independent humans complete the supplemental
usability protocol. Human trials should focus on expectations, terminology,
documentation order, self-repair confidence, and willingness to continue—not
repeat another artificial ten-person quota.

### First human trial and replacement candidate

The first independent human response completed the relocation, Registry,
TokaKV/WAL, compaction, modification, and ownership-repair path, but found a
new check/CodeGen consistency P1. A redundant second `.unwrap()` on the
non-nullable `LeasedLookupResult` intermediate passed `check` with no
diagnostic, then failed during CodeGen with `E0755` and an internal missing
symbol error. Splitting the expression, or using the valid single-unwrap chain,
worked. The report is public in
[Discussion #51](https://github.com/tokalang/toka/discussions/51#discussioncomment-18249448)
and the defect was tracked as
[tokalang/toka#52](https://github.com/tokalang/toka/issues/52).

This human finding invalidated candidate
`abea41db0566882486ac58b8ac9764102e456462`; it will never be tagged or
published. The semantic fallback had treated every missing `.unwrap()` method
as a nullable intrinsic, even when its receiver was not nullable. The fix
restricts the intrinsic to genuinely nullable receivers. Invalid redundant
chains now fail in semantic checking with `E0417`; valid Result/Option chains
and split-statement forms still check, compile, and run. The frozen
`0.9.9-16` interface key did not change.

The replacement unpublished RC13 candidate is
`3d32808a9f34e1fdf9c4c36dac9facc5284a0ac2`. It passed the full Linux x64,
Linux arm64, macOS x64, and macOS arm64 qualification plus the cross-target
summary, and retained four new temporary archives without creating a tag or
release: [replacement qualification run](https://github.com/tokalang/toka/actions/runs/33633120473).

| Replacement target | SHA-256 |
| :--- | :--- |
| Linux x64 | `041c55670481a05b03f53bd9636f82a512edcdfad3d7202255d4acb3325bb74a` |
| Linux arm64 | `68539be51e83a463096935bee74e5c03a7ee0ca95c1ae1414bad6cbfa984eee9` |
| macOS x64 | `fc5d4e1c375c4cbd1e85e7c2f10e0499061cf2bbbbbed3a96acb39cc9a032785` |
| macOS arm64 | `26fbe50b0c981b0e18070f3389b7c01236982e4da86cac748e97124170106aa3` |

Packaged macOS arm64 replay confirmed that the invalid TokaKV expression is
rejected consistently by `check` and `run` with no CodeGen internal error,
while the valid chained expression runs successfully. Human recruitment has
therefore resumed against the replacement SHA. The prior AI replay remains
useful product-path evidence, but publication still requires 3–5 human reports
against the replacement candidate with 0 P0/P1.
