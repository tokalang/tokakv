#!/usr/bin/env python3
import os
import sys
import subprocess
import tempfile

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TOKA_DIR = os.path.join(ROOT_DIR, "toka")
TOKAKV_DIR = os.path.join(ROOT_DIR, "tokakv")
TOKAC = os.path.join(TOKA_DIR, "build", "bin", "tokac")

def run_cmd(cmd, env=None):
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    return res

def main():
    print("=== [TokaKV Package Qualification Suite] ===")

    if not os.path.exists(TOKAC):
        print(f"Error: tokac compiler binary not found at {TOKAC}")
        sys.exit(1)

    tests = [
        ("memtable_v1", os.path.join(TOKAKV_DIR, "tests", "memtable_v1.tk")),
        ("wal_codec_edge_v1", os.path.join(TOKAKV_DIR, "tests", "wal_codec_edge_v1.tk")),
        ("wal_recovery_v1", os.path.join(TOKAKV_DIR, "tests", "wal_recovery_v1.tk")),
        ("wal_crc_tail_v1", os.path.join(TOKAKV_DIR, "tests", "wal_crc_tail_v1.tk")),
        ("wal_poison_and_open_v1", os.path.join(TOKAKV_DIR, "tests", "wal_poison_and_open_v1.tk")),
        ("sstable_writer_reader_v1", os.path.join(TOKAKV_DIR, "tests", "sstable_writer_reader_v1.tk")),
        ("sstable_corruption_v1", os.path.join(TOKAKV_DIR, "tests", "sstable_corruption_v1.tk")),
        ("manifest_recovery_v1", os.path.join(TOKAKV_DIR, "tests", "manifest_recovery_v1.tk")),
        ("manifest_corruption_v1", os.path.join(TOKAKV_DIR, "tests", "manifest_corruption_v1.tk")),
        ("block_cache_v1", os.path.join(TOKAKV_DIR, "tests", "block_cache_v1.tk")),
        ("concurrent_block_cache_v1", os.path.join(TOKAKV_DIR, "tests", "concurrent_block_cache_v1.tk")),
        ("concurrent_engine_read_write_v1", os.path.join(TOKAKV_DIR, "tests", "concurrent_engine_read_write_v1.tk")),
        ("merging_iterator_v1", os.path.join(TOKAKV_DIR, "tests", "merging_iterator_v1.tk")),
        ("l0_compaction_v1", os.path.join(TOKAKV_DIR, "tests", "l0_compaction_v1.tk")),
        ("compaction_crash_recovery_v1", os.path.join(TOKAKV_DIR, "tests", "compaction_crash_recovery_v1.tk")),
        ("release_failpoint_immunity_v1", os.path.join(TOKAKV_DIR, "tests", "release_failpoint_immunity_v1.tk")),
        ("concurrent_compaction_read_write_v1", os.path.join(TOKAKV_DIR, "tests", "concurrent_compaction_read_write_v1.tk")),
        ("wal_rotation_multi_gen_v1", os.path.join(TOKAKV_DIR, "tests", "wal_rotation_multi_gen_v1.tk")),
        ("wal_manifest_migration_v1", os.path.join(TOKAKV_DIR, "tests", "wal_manifest_migration_v1.tk")),
        ("wal_rotation_crash_recovery_v1", os.path.join(TOKAKV_DIR, "tests", "wal_rotation_crash_recovery_v1.tk")),
        ("concurrent_wal_rotation_read_write_v1", os.path.join(TOKAKV_DIR, "tests", "concurrent_wal_rotation_read_write_v1.tk")),
        ("snapshot_mvcc_memtable_v1", os.path.join(TOKAKV_DIR, "tests", "snapshot_mvcc_memtable_v1.tk")),
        ("snapshot_lease_raii_v1", os.path.join(TOKAKV_DIR, "tests", "snapshot_lease_raii_v1.tk")),
        ("snapshot_sstable_mvcc_v1", os.path.join(TOKAKV_DIR, "tests", "snapshot_sstable_mvcc_v1.tk")),
        ("manifest_v2_to_v3_migration_v1", os.path.join(TOKAKV_DIR, "tests", "manifest_v2_to_v3_migration_v1.tk")),
        ("snapshot_dynamic_capacity_and_reuse_v1", os.path.join(TOKAKV_DIR, "tests", "snapshot_dynamic_capacity_and_reuse_v1.tk")),
        ("snapshot_multiple_queries_and_compaction_v1", os.path.join(TOKAKV_DIR, "tests", "snapshot_multiple_queries_and_compaction_v1.tk")),
        ("l0_to_l1_multi_sstable_partitioning_v1", os.path.join(TOKAKV_DIR, "tests", "l0_to_l1_multi_sstable_partitioning_v1.tk")),
        ("l0_to_l1_overlap_and_untouched_l1_v1", os.path.join(TOKAKV_DIR, "tests", "l0_to_l1_overlap_and_untouched_l1_v1.tk")),
        ("tombstone_gc_whole_group_and_empty_output_v1", os.path.join(TOKAKV_DIR, "tests", "tombstone_gc_whole_group_and_empty_output_v1.tk")),
        ("l1_compaction_failpoint_crash_recovery_v1", os.path.join(TOKAKV_DIR, "tests", "l1_compaction_failpoint_crash_recovery_v1.tk")),
        ("concurrent_snapshot_leveled_compaction_v1", os.path.join(TOKAKV_DIR, "tests", "concurrent_snapshot_leveled_compaction_v1.tk")),
    ]

    tsan_tests = [
        ("concurrent_block_cache_v1", os.path.join(TOKAKV_DIR, "tests", "concurrent_block_cache_v1.tk")),
        ("concurrent_engine_read_write_v1", os.path.join(TOKAKV_DIR, "tests", "concurrent_engine_read_write_v1.tk")),
        ("concurrent_compaction_read_write_v1", os.path.join(TOKAKV_DIR, "tests", "concurrent_compaction_read_write_v1.tk")),
        ("concurrent_wal_rotation_read_write_v1", os.path.join(TOKAKV_DIR, "tests", "concurrent_wal_rotation_read_write_v1.tk")),
        ("concurrent_snapshot_leveled_compaction_v1", os.path.join(TOKAKV_DIR, "tests", "concurrent_snapshot_leveled_compaction_v1.tk")),
    ]

    diag_tests = [
        ("diag_block_cache_private_fields", os.path.join(TOKAKV_DIR, "tests", "diag_block_cache_private_fields.tk"), "E0418"),
        ("diag_block_cache_cannot_mutate_entries", os.path.join(TOKAKV_DIR, "tests", "diag_block_cache_cannot_mutate_entries.tk"), "E0418"),
        ("diag_block_cache_cannot_mutate_inner", os.path.join(TOKAKV_DIR, "tests", "diag_block_cache_cannot_mutate_inner.tk"), "E0418"),
        ("diag_engine_private_fields", os.path.join(TOKAKV_DIR, "tests", "diag_engine_private_fields.tk"), "E0418"),
        ("diag_engine_writer_state_private_fields", os.path.join(TOKAKV_DIR, "tests", "diag_engine_writer_state_private_fields.tk"), "E0418"),
        ("diag_guard_not_send", os.path.join(TOKAKV_DIR, "tests", "diag_guard_not_send.tk"), "E0477"),
        ("diag_guard_outlives_mutex", os.path.join(TOKAKV_DIR, "tests", "diag_guard_outlives_mutex.tk"), "E0455"),
        ("diag_borrow_outlives_guard", os.path.join(TOKAKV_DIR, "tests", "diag_borrow_outlives_guard.tk"), "E0455"),
        ("diag_snapshot_lease_cannot_forge", os.path.join(TOKAKV_DIR, "tests", "diag_snapshot_lease_cannot_forge.tk"), "E0418"),
        ("diag_snapshot_lease_cannot_call_internal_create", os.path.join(TOKAKV_DIR, "tests", "diag_snapshot_lease_cannot_call_internal_create.tk"), "E04551"),
        ("diag_snapshot_registry_cannot_acquire_lease", os.path.join(TOKAKV_DIR, "tests", "diag_snapshot_registry_cannot_acquire_lease.tk"), "E0417"),
        ("diag_snapshot_capability_cannot_grant", os.path.join(TOKAKV_DIR, "tests", "diag_snapshot_capability_cannot_grant.tk"), "E04551"),
        ("diag_snapshot_capability_cannot_forge", os.path.join(TOKAKV_DIR, "tests", "diag_snapshot_capability_cannot_forge.tk"), "E0418"),
    ]

    passed = 0
    failed = 0

    clang_bin = "clang"
    if os.path.exists("/opt/homebrew/opt/llvm/bin/clang"):
        clang_bin = "/opt/homebrew/opt/llvm/bin/clang"

    openssl_inc = []
    openssl_lib = []
    if os.path.exists("/opt/homebrew/include"):
        openssl_inc = ["-I/opt/homebrew/include"]
        openssl_lib = ["-L/opt/homebrew/lib", "-lssl", "-lcrypto"]

    with tempfile.TemporaryDirectory() as tmp_dir:
        # 1. Build Release runtime object (WITHOUT -DTOKA_TESTING)
        rt_release_obj = os.path.join(tmp_dir, "toka_rt_release.o")
        rt_rel_res = run_cmd([
            clang_bin, "-DTOKA_HAS_OPENSSL=1"
        ] + openssl_inc + [
            "-g", "-c",
            os.path.join(TOKA_DIR, "lib", "sys", "toka_rt.c"),
            "-o", rt_release_obj
        ])
        if rt_rel_res.returncode != 0:
            print(f"[FATAL] Failed to build Release runtime object:\n{rt_rel_res.stderr}")
            sys.exit(1)

        # 2. Build Testing runtime object (with -DTOKA_TESTING=1)
        rt_testing_obj = os.path.join(tmp_dir, "toka_rt_testing.o")
        rt_t_res = run_cmd([
            clang_bin, "-DTOKA_HAS_OPENSSL=1", "-DTOKA_TESTING=1"
        ] + openssl_inc + [
            "-g", "-c",
            os.path.join(TOKA_DIR, "lib", "sys", "toka_rt.c"),
            "-o", rt_testing_obj
        ])
        if rt_t_res.returncode != 0:
            print(f"[FATAL] Failed to build Testing runtime object:\n{rt_t_res.stderr}")
            sys.exit(1)

        # 3. Build ASan runtime object (with -DTOKA_TESTING=1)
        rt_asan_obj = os.path.join(tmp_dir, "toka_rt_asan.o")
        rt_res = run_cmd([
            clang_bin, "-DTOKA_HAS_OPENSSL=1", "-DTOKA_TESTING=1"
        ] + openssl_inc + [
            "-fsanitize=address", "-g", "-c",
            os.path.join(TOKA_DIR, "lib", "sys", "toka_rt.c"),
            "-o", rt_asan_obj
        ])
        if rt_res.returncode != 0:
            print(f"[FATAL] Failed to build ASan runtime object:\n{rt_res.stderr}")
            sys.exit(1)

        # 4. Build TSan runtime object (with -DTOKA_TESTING=1)
        rt_tsan_obj = os.path.join(tmp_dir, "toka_rt_tsan.o")
        rt_tsan_res = run_cmd([
            clang_bin, "-DTOKA_HAS_OPENSSL=1", "-DTOKA_TESTING=1"
        ] + openssl_inc + [
            "-fsanitize=thread", "-g", "-c",
            os.path.join(TOKA_DIR, "lib", "sys", "toka_rt.c"),
            "-o", rt_tsan_obj
        ])
        if rt_tsan_res.returncode != 0:
            print(f"[FATAL] Failed to build TSan runtime object:\n{rt_tsan_res.stderr}")
            sys.exit(1)

        # 5. Standard & ASan Tests
        for name, test_path in tests:
            bin_path = os.path.join(tmp_dir, name)
            obj_path = os.path.join(tmp_dir, f"{name}.o")
            asan_bin_path = os.path.join(tmp_dir, f"{name}_asan")

            # Compile Toka source to object file
            comp_obj = run_cmd([
                TOKAC,
                "-I", os.path.join(TOKA_DIR, "lib"),
                "-I", os.path.join(TOKAKV_DIR, "lib"),
                test_path,
                "-c", "-o", obj_path
            ])
            if comp_obj.returncode != 0:
                print(f"[FAILED] Compilation failed for {name}:\n{comp_obj.stderr}")
                failed += 1
                continue

            if name == "release_failpoint_immunity_v1":
                print(f"-> Building and running {name} (release profile verification)...", flush=True)
                # Link strictly with Release runtime (where TOKA_TESTING is absent)
                link_rel = run_cmd([
                    clang_bin, obj_path, rt_release_obj
                ] + openssl_lib + [
                    "-lpthread", "-lm", "-o", bin_path
                ])
                if link_rel.returncode != 0:
                    print(f"[FAILED] Release linking failed for {name}:\n{link_rel.stderr}")
                    failed += 1
                    continue
                exec_res = run_cmd([bin_path])
                if exec_res.returncode != 0:
                    print(f"[FAILED] Release profile immunity failed for {name} (exit code {exec_res.returncode}):\n{exec_res.stderr}")
                    failed += 1
                    continue
                print(f"[PASSED] {name} verified release profile immunity cleanly.", flush=True)
                passed += 1
                continue

            print(f"-> Building and running {name} (standard & ASan)...", flush=True)

            # Link standard test binary with Testing runtime
            link_std = run_cmd([
                clang_bin, obj_path, rt_testing_obj
            ] + openssl_lib + [
                "-lpthread", "-lm", "-o", bin_path
            ])
            if link_std.returncode != 0:
                print(f"[FAILED] Standard linking failed for {name}:\n{link_std.stderr}")
                failed += 1
                continue

            # Execute standard binary
            exec_res = run_cmd([bin_path])
            if exec_res.returncode != 0:
                print(f"[FAILED] Execution failed for {name} (exit code {exec_res.returncode}):\nSTDOUT:\n{exec_res.stdout}\nSTDERR:\n{exec_res.stderr}")
                failed += 1
                continue

            # Link with ASan
            link_asan = run_cmd([
                clang_bin, "-fsanitize=address",
                obj_path, rt_asan_obj
            ] + openssl_lib + [
                "-lpthread", "-lm",
                "-o", asan_bin_path
            ])
            if link_asan.returncode != 0:
                print(f"[FAILED] ASan linking failed for {name}:\n{link_asan.stderr}")
                failed += 1
                continue

            # Execute under ASan
            asan_exec = run_cmd([asan_bin_path])
            if asan_exec.returncode != 0:
                print(f"[FAILED] ASan execution failed for {name} (exit code {asan_exec.returncode}):\nSTDOUT:\n{asan_exec.stdout}\nSTDERR:\n{asan_exec.stderr}")
                failed += 1
                continue

            print(f"[PASSED] {name} passed standard + ASan cleanly.", flush=True)
            passed += 1

        # 4. Fully Instrumented TSan Tests (Toka LLVM IR + Clang TSan instrumentation)
        for tsan_name, concurrent_test_path in tsan_tests:
            print(f"-> Building and running {tsan_name} (TSan fully instrumented)...", flush=True)
            concurrent_ll_path = os.path.join(tmp_dir, f"{tsan_name}.ll")
            concurrent_tsan_obj = os.path.join(tmp_dir, f"{tsan_name}_tsan.o")
            tsan_bin_path = os.path.join(tmp_dir, f"{tsan_name}_tsan_bin")

            # Emit LLVM IR for Toka test and library code
            emit_ll_res = run_cmd([
                TOKAC,
                "-I", os.path.join(TOKA_DIR, "lib"),
                "-I", os.path.join(TOKAKV_DIR, "lib"),
                "--emit-llvm",
                concurrent_test_path,
                "-o", concurrent_ll_path
            ])
            if emit_ll_res.returncode != 0:
                print(f"[FAILED] Failed to emit LLVM IR for {tsan_name} TSan:\n{emit_ll_res.stderr}")
                failed += 1
            else:
                # Compile Toka LLVM IR through Clang with -fsanitize=thread to instrument all Toka functions & memory accesses
                tsan_obj_res = run_cmd([
                    clang_bin, "-fsanitize=thread", "-g", "-c",
                    concurrent_ll_path,
                    "-o", concurrent_tsan_obj
                ])
                if tsan_obj_res.returncode != 0:
                    print(f"[FAILED] Clang TSan compilation of {tsan_name} Toka LLVM IR failed:\n{tsan_obj_res.stderr}")
                    failed += 1
                else:
                    # Link instrumented Toka object with instrumented runtime object
                    link_tsan = run_cmd([
                        clang_bin, "-fsanitize=thread",
                        concurrent_tsan_obj, rt_tsan_obj
                    ] + openssl_lib + [
                        "-lpthread", "-lm",
                        "-o", tsan_bin_path
                    ])
                    if link_tsan.returncode != 0:
                        print(f"[FAILED] TSan linking failed for {tsan_name}:\n{link_tsan.stderr}")
                        failed += 1
                    else:
                        tsan_exec = run_cmd([tsan_bin_path])
                        if tsan_exec.returncode != 0:
                            print(f"[FAILED] TSan execution failed for {tsan_name} (exit code {tsan_exec.returncode}):\n{tsan_exec.stderr}")
                            failed += 1
                        else:
                            print(f"[PASSED] {tsan_name} passed full TSan instrumentation cleanly.", flush=True)
                            passed += 1

        # 5. Diagnostic Compile-Fail Tests
        for diag_name, diag_path, expected_err in diag_tests:
            print(f"-> Running diagnostic compile-fail test {diag_name} (expecting {expected_err})...", flush=True)
            diag_bin = os.path.join(tmp_dir, diag_name)
            diag_res = run_cmd([
                TOKAC,
                "-I", os.path.join(TOKA_DIR, "lib"),
                "-I", os.path.join(TOKAKV_DIR, "lib"),
                diag_path,
                "-o", diag_bin
            ])
            if diag_res.returncode == 0:
                print(f"[FAILED] Expected {diag_name} to fail compilation, but it succeeded!")
                failed += 1
            elif expected_err not in diag_res.stderr:
                print(f"[FAILED] Expected error {expected_err} in {diag_name}, got:\n{diag_res.stderr}")
                failed += 1
            else:
                print(f"[PASSED] {diag_name} compile-fail verified cleanly with '{expected_err}'.", flush=True)
                passed += 1

    print(f"\n--- TokaKV Package Qualification Results: {passed} Passed, {failed} Failed ---", flush=True)
    if failed > 0:
        sys.exit(1)
    print("=== ALL TOKAKV QUALIFICATION TESTS PASSED! ===", flush=True)

if __name__ == "__main__":
    main()
