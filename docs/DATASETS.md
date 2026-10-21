# Datasets

## What we build on

| Use | Source | Level | Period | Licence |
|---|---|---|---|---|
| Training labels | CCHAIN `disease_pidsr_totals`, all 12 cities | City, weekly (Mon) | 2008-01-07 to 2022-12-26 | CC BY 4.0 |
| Training rain | CCHAIN climate tables | Barangay, daily | 2003-2022 | CC BY 4.0 |
| Replay rain | CHIRPS v2 daily (Earth Engine) | 0.05° | 1981 to ~1.5 months ago | Public domain |
| Static barangay layers | CCHAIN `project_noah_hazards` (2015), `google_open_buildings` (2023), `location` | Barangay (14, pre-2018) | Static | CC BY 4.0 |
| Health facilities | HOT OSM export via HDX | Point | Refreshed weekly upstream | ODbL |
| Population | PSA 2024 POPCEN | Barangay (18) | 1 Jul 2024 | Public |
| Codes | PSA PSGC | Barangay | 2023 codes, unchanged since | Public |
| Polygons | faeldon/philippines-json-maps 2023 (PSA/NAMRIA boundaries) | Barangay (18) | 2023 | MIT |
| Flood + gate log | DROMIC, MMDA, news (hand-built) | Barangay, per event | 2024 first, back to 2015 later | Public documents, cite each row |

## Why this set

- Everything is open and downloadable in a day. Nothing on the Sprint 1 path waits on a request letter.
- CCHAIN is already keyed by PSGC and Monday weeks, so joins are cheap.
- The flood and gate log is the part other teams won't have, and it's what makes the 2024 replay credible: the Tanza/Tangos gate was down from June 2024, so Carina flooding there was tide-driven as much as rain-driven.

## What the labels can and can't do

Navotas PIDSR, 2008-2022: 471 cases, 780 weeks, 74.6% zero weeks. 76 weeks with ≥ 2 cases, 40 with ≥ 3, 16 with ≥ 5. About 80% of cases fall July-October. City level only, nothing after 2022.

Consequences:

- **Target** is P(cases ≥ 3) per week. ≥ 2 is the sensitivity run. Counts are secondary.
- **Pool** the 12 CCHAIN cities. Navotas alone has ~40 positive weeks.
- **Baselines**: B0 all-zero, B1 5-year same-week median, B2 seasonal NB GLM. On the 2021-22 holdout B0 scores MAE 0.490 and B1 0.481; a same-week *mean* does worse (0.519). Anything we claim has to beat these on the metrics that matter for action.
- **Primary metrics**: Brier, AUC, episode recall, median lead time. MAE secondary, on all weeks and non-zero weeks.
- **Barangay validation** can't use CCHAIN PIDSR (city code only). Until CESU data arrives, the index is checked against flood-event frequency from our log, and presented as a planning aid.
- **2020-2021** are COVID years with under-reporting (2020: 10 cases). Flag them.

## Known traps

- **14 vs 18 barangays.** CCHAIN has the 14 pre-2018 units. Tangos, Tanza and NBBS were split in Jan 2018 into Tangos North/South, Tanza 1/2 and NBBS Dagat-dagatan/Kaunlaran/Proper. Everything is keyed on 10-digit PSGC through `f2f.barangays` (see below). Parent percentages and densities are copied to each child; parent counts are split by population share. Switch to building-footprint shares if that split visibly distorts the ranking.
- **Never sum PIDSR and FHSIS.** PIDSR is already inside FHSIS annual totals.
- **CHIRPS vs CCHAIN rain.** We train on one and replay on the other. Check the distributions match over 2015-2022 before trusting the replay.
- **Reporting delay.** DOH totals for the same period get revised upward for weeks. Recent case counts are never a forecast feature without a delay offset.
- **Licences.** LiPAD: internal only, no redistribution. Global Flood Database: CC BY-NC. OSM-derived layers: ODbL share-alike.

## Barangay reference table

`src/f2f/ref/navotas_barangays.csv`, loaded with `f2f.barangays.load()`. This is the only data file in git: 18 rows of public facts that every layer joins on.

| Column | Source |
|---|---|
| `psgc10`, `corr_code`, `name` | PSA PSGC. PSA's site blocks scripted access, so codes were taken from two mirrors that agree: [jeffreybernadas/psgc-api](https://github.com/jeffreybernadas/psgc-api) and [faeldon/philippines-json-maps](https://github.com/faeldon/philippines-json-maps) (2023 PSGC) |
| `parent_psgc_cchain` | CCHAIN `location` table (14 pre-2018 units, `PH137503001`…`PH137503014`) |
| `pop_2020` | PSA 2020 CPH, per barangay. Sums to 247,543 |
| `pop_2024` | PSA 2024 POPCEN via [CityPopulation.de](https://www.citypopulation.de/en/philippines/navotas/). Sums to 252,878 |

PSA reports 2024 counts for Tangos, Tanza and NBBS only as the old parents. Their children get `parent_2024 × child's 2020 share`, rounded so the parent totals stay exact. `pop_2024_source = parent_2024_x_2020_share` marks those 7 rows. Replace them when per-barangay 2024 figures for the split barangays turn up.

Split barangays got new codes 015-018. The parent's old code stays with the first child: 009 NBBS Kaunlaran, 013 Tangos South, 014 Tanza 1.

Config lists that name barangays (`gate_impaired.barangays`, `exposure.nfpc_barangays`) use `psgc10`, not names.

## Barangay index inputs

`python -m f2f.ingest.static` downloads these into `data/raw/`. URLs are pinned to a commit where possible.

- **CCHAIN tables** come from a public mirror (`jairo3224/Leptospiros_Case_Estimation`) until someone pulls the official Kaggle files in #1. The tables are the same CCHAIN release; swap the URL in `ingest/static.py` when the official ones arrive.
- **Polygons:** `faeldon/philippines-json-maps`, 2023, medium resolution, all 18 barangays with `adm4_psgc`. HDX COD-AB is the official alternative (#2).
- **Health facilities:** HOT OSM. The city tags in this export are wrong in places (Navotas City Hospital is tagged Caloocan), so facilities are picked by distance, not by city.

The indicators and the scaling are listed in the `src/f2f/index.py` docstring. Known weak spots:

- **Split children inherit parent values.** NOAH flood shares and building stats exist only for CCHAIN's 14 units, so children of Tangos, Tanza and NBBS inherit the parent's numbers. Their population, density and distance to care are their own.
- **Distance to care is OSM-limited.** OSM maps few barangay health centres in Navotas, so `km_to_care` under-counts real access in some barangays. The upgrade is the CLUP Table 3.7 facility list plus walking time.
- **Gate flag is time-limited.** `gate_affected` only switches on when the scenario config has a `gate_impaired` list (Carina 2024 does). Without it the indicator is constant and drops out.
- **No outcome validation yet.** Weights are equal and there are no barangay case counts to check against. Treat the ranking as a planning aid.

## Daytime exposure (scenario)

`f2f.exposure.present_population(cfg)` gives `pop_daytime = pop_2024 × 0.93 + fish port inflow`.

- **0.93** is Navotas's day/night ratio from JICA MUCEP (194.4k by day vs 209.4k at night, 2012-14 survey).
- **Inflow** is 30k, 40k or 50k Navotas Fish Port Complex workers (DA, Jul 2026: "at least 30,000, about 50,000 at peak"). `exposure.nfpc_scenario` in config picks one.
- **Placement:** the inflow is split equally across the three NBBS barangays. The port's industrial strip in NBBN, Bangculasi and San Rafael Village gets none for now. Weighting by CLUP industrial land area is the upgrade.

The dashboard labels every daytime number as a scenario estimate.

## Not used in Sprint 1

Matsushita San Lazaro series (2001-2012), UHSLC/IOC tide, GSMaP/IMERG, ECMWF forecast rain, PAGASA station data, WorldPop/HRSL age layers, Open Buildings, MUCEP OD data, PFDA port volumes. Most come in Sprint 2 if they earn their place on the demo path.

## Requests out (send day 1)

| To | Ask for | Why |
|---|---|---|
| DOH-MMCHD RESU | Weekly lepto cases by NCR city, 2008-2026; city epidemic thresholds | CAMANAVA pooling, a real 2023-26 test |
| Navotas CESU/CHO | Barangay-by-week PIDSR counts 2015-2026; 2018 outbreak barangay names; doxycycline inventory | Barangay validation, real stock baseline |
| DOH FOI portal | Two existing requests on NCR weekly lepto data, check attachments | Possible free 2021-25 labels |

Turnaround is 15-20 working days. Build as if none of it arrives.
