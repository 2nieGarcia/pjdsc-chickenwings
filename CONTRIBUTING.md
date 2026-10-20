# Working in this repo

## Branches and PRs

`main` always runs. Branch naming, claiming issues, PR rules and the Definition of Done are in [docs/WORKFLOW.md](docs/WORKFLOW.md). Short version: `feat/<issue>-<short-name>`, one issue at a time, `Closes #N` in the PR.

## Commits

Conventional prefix, lowercase, imperative, no period. Say what changed and, if it isn't obvious, why. Keep the subject under ~70 chars and put details in the body.

Prefixes we use: `feat`, `fix`, `data`, `model`, `docs`, `test`, `refactor`, `chore`.

Good:

```
feat(planner): greedy allocation by tier, cap at usable stock
fix(features): rain lag 2 was leaking into h=3
data: add carina 2024 flood log rows from DROMIC report 8
model: freeze alert cutoff at 0.35 (best F2 on 2019-20)
test(contracts): reject forecasts with rain_through after issue_date
chore: pin pyarrow, 17 broke parquet dates on windows
docs: note 14 vs 18 barangay split in DATASETS
```

Not good:

```
update
fixed stuff
WIP
feat: Implemented the comprehensive barangay index module.
```

Squash your WIP commits before merging. Don't rewrite `main`.

## Before you push

- `pytest -q` passes.
- Artifact shape changed? Update `src/f2f/contracts.py` and `docs/CONTRACTS.md` together.
- New source? Add a row to `docs/DATASETS.md` with licence and access date.
- Nothing from `data/` or `CONFIDENTIAL/` is staged (`git status` before every commit).

## Notebooks

Fine for exploration under `notebooks/`. Clear outputs before committing. Anything the pipeline needs moves into `src/f2f/`.
