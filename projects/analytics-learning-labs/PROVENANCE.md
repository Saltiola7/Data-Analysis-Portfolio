# Analytics Learning Labs Provenance

## Clean-room boundary

Five historical notebooks were reviewed privately as theme-only inputs. Their
code, prose, datasets, outputs, schemas, metrics, and execution history were not
copied and were not migrated. Automatic Jupyter-to-Marimo conversion was used
only as a local admission diagnostic; no converted source or rendered output
entered this project.

Every public successor has newly written behavior, interfaces, contracts, code,
tests, documentation, and deterministic synthetic fixtures.

| Private theme-only input | Retained general question | Independently implemented public successor |
|---|---|---|
| `airline.ipynb` | How can delay components and cancellations be summarized without losing flight grain? | `apps/airline_delays.py` |
| `cancer-patient-dataset.ipynb` | How should repeated profiles and ordinal associations be communicated safely? | `apps/synthetic_cohort.py` |
| `mcdonalds.ipynb` | How can location records be validated while preserving unresolved evidence? | `apps/restaurant_locations.py` |
| `notebook.ipynb` | How can catalog duration and genre patterns be explored at title grain? | `apps/streaming_catalog.py` |
| `winning-medal-in-judo.ipynb` | How can sports outcomes be summarized at explicit athlete-event grain? | `apps/sports_outcomes.py` |

The table records conceptual ancestry only. The private filenames are not
runtime dependencies, public files, redistributable sources, or authorship
evidence.

## Public fixture lineage

| Lab | Generator | Default rows | Canonical grain | Public data decision |
|---|---|---:|---|---|
| Airline Delay Quality Lab | `generate_airline_fixture` | 160 | Unique fictional `flight_id`; completed-flight delay means exclude explicit cancelled-row zero placeholders | Newly generated synthetic data |
| Synthetic Health Risk Quality Lab | `generate_cohort_fixture` | 180 | Unique fictional `record_id`; agreeing repeats deduplicate to `profile_key`, conflicting repeats fail validation; risk bands are assigned independently from the analyzed score composite | Newly generated synthetic data |
| Restaurant Location Quality Lab | `generate_restaurant_fixture` | 140 | Unique fictional `record_id`; bounded missing-coordinate examples exercise the unresolved ledger | Newly generated synthetic data |
| Streaming Catalog Explorer | `generate_streaming_fixture` | 180 | Unique fictional `title_id` | Newly generated synthetic data |
| Judo Medal Explorer | `generate_sports_fixture` | 220 | Unique fictional `event_id`; repeated athlete identifiers retain stable team, continent, and weight class | Newly generated synthetic data |

### Default fixture identity

All defaults use generator version `analytics-learning-labs/1.0`, seed `2026`,
and on-demand generation. The admission review date is `2026-07-30`; no
generated dataset is stored in the repository.

| Lab | Default canonical CSV SHA-256 |
|---|---|
| Airline Delay Quality Lab | `d8a745bbc8c53e973328fe0e83b2fcc9fc36b45cd70fbc0f6ee9f87ce157d6fb` |
| Synthetic Health Risk Quality Lab | `5aa30097da9a8f47c9c2cb17e73c4bcd0d6938640de7e81d154d72e7cd83fdbc` |
| Restaurant Location Quality Lab | `7e8ef86c9729ccc136698165234afbcf18ce5172077f2c0615642a02d6fe7e9e` |
| Streaming Catalog Explorer | `223f9931a90bb95e1e65425c6f8998c345a723a01740609ce36ba5c292f18228` |
| Judo Medal Explorer | `4713eb2e3d93a9ecf7a2215cffcc7b665fa1c56d5d18d3cf3e7282b99db87977` |

Fixture generation is deterministic for generator version, integer seed, and
row count. Each generated frame exposes a SHA-256 over its canonical CSV
serialization, and the five default hashes are pinned in the fixture tests.
Changing a default fixture requires an explicit generator-version and
provenance review. Identifiers and labels are fictional. No generator reads a
file, network service, environment variable, credential store, telemetry
endpoint, or private module.

### Transformation, privacy, and redistribution

The transformation chain is generator → schema/grain/value validation →
lab-specific aggregation → accessible metrics, table, and chart evidence. The
health lab additionally audits agreeing duplicate profiles before
deduplication; the restaurant lab partitions accepted and unresolved records
without imputation.

Privacy classification is public synthetic data with no person, client,
employer, assessment, or credential record. Generator source and independently
written app logic are redistributed under the repository MIT license; generated
rows are transient reproducibility evidence rather than a published dataset.
The retained authority is generator code, contracts, version, default hashes,
tests, and this record.

## Certification assessment boundary

Private certification files were reviewed only to identify broad competency
areas. Assessment prompts, supplied datasets, solutions, schemas, metrics,
outputs, grader rules, and private assessment history remain outside the
repository. No assessment implementation or supplied record was translated,
sanitized, or repackaged as a learning lab.

The two owner-provided screenshots of issuer-issued credentials documented in
[CERTIFICATIONS.md](../../CERTIFICATIONS.md) are separate professional
evidence. They are not source data, do not supply app behavior, and do not
weaken the assessment boundary.

## Claim and safety review

- Learning labs are presented below the three flagships and described as
  supporting demonstrations.
- No lab claims production deployment, benchmark superiority, or external
  validity.
- Health-lab language is descriptive and educational. It makes no clinical,
  diagnostic, treatment, predictive, or causal claim.
- Every app exposes its fixture identity, analytical grain, limitations, and
  visible evidence.

## Retention and replacement

Only independently written public source and deterministic synthetic generation
logic are retained. Private inputs remain outside public history. If provenance
becomes uncertain, the affected Molab link is removed first and the lab is
retired until a new clean-room review can establish its lineage.

## License

New source, tests, and documentation are owner-authored and covered by the
repository's MIT license. Historical notebooks, assessment material, and any
third-party data remain excluded and receive no redistribution claim.
