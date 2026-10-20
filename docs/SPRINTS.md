# Sprints

## Sprint 1: PoC (7 days)

### The demo we're building toward

"Carina, two weeks early." Drag the issue-date slider from 1 Jul to 15 Aug 2024:

1. Weekly rain bars climb into the 22-26 Jul event.
2. The gate-impaired flag is already on for Tanza 1/2, Tangos North/South and San Jose; it has been since June.
3. P(elevated week) crosses the alarm line around the event, before the August hospital-surge headlines.
4. The barangay map reshuffles tiers. Rank bands show which positions are solid and which are a coin flip.
5. Flip exposure from resident to daytime. Fish port workers land on the NBBS barangays and capsule need jumps roughly tenfold.
6. Stock panel: need vs usable stock (labelled synthetic), what's unmet, where. The duty officer types a name and approves. It goes in the audit log. Nothing is dispatched.

Close on the backtest card: on MAE, "predict zero" wins; on episode recall and lead time, it never warns anyone. That's why the output is a probability.

### Lanes

| Day | A: data | B: model | C: index + planner | D: app | E: comms + requests |
|---|---|---|---|---|---|
| 1 | Pull CCHAIN. Check for Navotas A27 rows by barangay. Check COD-AB has all 18 | Profile the panel, list episodes | PSGC 14→18 crosswalk | App shell, map from GeoJSON | Send MMCHD and CESU letters, check FOI pages |
| 2 | C1 builder | B0/B1/B2 + backtest harness | Hazard and exposure from CCHAIN + POPCEN | Load C2/C3 fixtures | Carina flood/gate log: dates, barangays, sources |
| 3 | CHIRPS 2015-24, overlap check vs CCHAIN rain | Pooled event model, h = 1/2/3 | Geometric mean + MC rank bands | Slider + timeline | Deck skeleton |
| 4 | Log → C1 flags | Freeze cutoff on 2019-20, score 2021-22 once | Wire planner to C3 | Tier map + top drivers | Demo script v1 |
| 5 | Generate replay issues | Write C2 for the replay | Daytime scenario (0.93 + NFPC 30k/40k/50k) | Stock panel + approve | Dry run |
| 6 | Bug bash | Metrics card | Sensitivity summary | Polish, offline check | Dry run 2 |
| 7 | Freeze `run_id`, tag `v0.1-poc` | | | | Record backup video |

### Done means

- `pytest -q` green.
- `python -m f2f.run --config configs/carina_2024.yaml` builds every artifact from a clean `data/raw/`.
- App runs with Wi-Fi off.
- Metrics table shows our model next to B0, B1 and B2, including where we lose.

### Cut first if late

Map polish, then sensitivity summary, then the daytime toggle. Never cut the baselines or the approve step.

## Sprint 2+

Kept loose on purpose. Re-plan at the end of each sprint.

- **S2:** LightGBM on the pooled panel (monotone on rain lags 1-3) as an ensemble member. Tide and spring-tide features from UHSLC. Conformal intervals. Check the lag shape against the Matsushita San Lazaro series.
- **S3:** If MMCHD or CESU data lands, run a real 2023-26 test and barangay Spearman. If not, validate the index against flood-event frequency and say so plainly.
- **S4:** Advisory preview, responsible-use page, rehearsals. Anything not on the demo path gets cut.
