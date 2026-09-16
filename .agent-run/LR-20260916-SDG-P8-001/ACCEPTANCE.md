# Acceptance

Five canonical files, explicit basis/heights, immutable input and exclusive output.
GeoJSON/DXF match the manual canonical pipeline, all files deterministic across directories.
Verify checks strict file set, regular files, schema, canonical bytes, hashes, references,
authoritative constraints and replayed Search semantics, including zero accepted.
Catchable failures leave no final package and clean owned staging files.
Required Python/Web/resource/mutation/CI/boundary gates must be evidenced, never inferred.

## Executed mapping

| Packet gate | Evidence in tests |
| --- | --- |
| P8-PY-01 / 07 / 08 | manifest_structure_hashes_and_references, reference_guard_independently |
| P8-PY-02 / 18 | same_inputs_different_directories_all_exact_bytes |
| P8-PY-03 / 04 | manual_cli_equivalence, both formats |
| P8-PY-05 / 06 | explicit_area_basis_and_canonical_heights |
| P8-PY-09 / 10 | existing_output_rejected_before_core, real symlinks |
| P8-PY-11 | stage_failure_is_atomic_and_preserves_inputs, interrupt cleanup |
| P8-PY-12 / 13 | exact_artifact_byte_tamper_detected, manifest_hash_tamper_detected |
| P8-PY-14 / 15 | missing_file_detected, strict_file_set_includes_hidden_metadata |
| P8-PY-16 | path/metadata leak mutations and no-input-name/path manifest test |
| P8-PY-17 | zero_accepted_is_completed_verified_package |

Additional checks cover native target races, reparse files, false but internally coherent
constraints, Search semantics, explicit input errors, malformed JSON and stdout privacy.
All local gates PASS; branch CI and Draft delivery are reported separately after this seal.
