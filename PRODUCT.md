# Product

## Platform

web

## Stack

Static web app: plain HTML/JS built with Vite, GSAP and three.js bundled locally so it runs offline. The Python pipeline (`src/f2f/`) stays the source of truth and exports its artifacts as JSON for the front end. The stock planner and approval log keep running in Python behind a small local endpoint. The Streamlit app (`app/streamlit_app.py`) stays as a fallback until the new front end is approved.

## Users

- **First:** PJDSC 2026 judges watching a live 5-minute demo. They have to believe the tool is real and useful, quickly.
- **Framed as:** the Navotas City Health Office (CHO) duty officer and DRRM staff who would use it weekly during the rainy season, to decide where to send alerts, staff and doxycycline before hospitals fill.

## Product Purpose

Flood-to-Fever is a leptospirosis early-warning and decision-support tool for Navotas City. Each week it answers four questions for the CHO:

1. How likely is an elevated week (≥ 3 reported cases) 1–3 weeks out?
2. Which of the 18 barangays go first?
3. Who is exposed but doesn't live there (fish port workers)?
4. Is there enough doxycycline, and who approves the plan?

Success in the demo is the Carina 2024 replay. As the issue date moves through July and August 2024, the alarm should rise before the hospital surge. The barangay tiers shift, the stock gap shows what's unmet, and an official approves a plan.

## Positioning

- **It's honest about the signal.** It forecasts the probability of an elevated week, not a case count, because "predict zero" beats count models on Navotas's sparse data (471 cases in 780 weeks).
- **It uses local drivers nobody else models:**
  - the Tangos–Tanza navigational gate failure (June 2024 to about August 2025);
  - a hand-built flood log;
  - the fish port daytime population.
- **It ranks barangays with uncertainty bands,** not single numbers, using an INFORM-style index (hazard, exposure, vulnerability, coping gap).

## Operating Context

- **Demo:** a single laptop, often with no Wi-Fi, run by the team at the PJDSC 2026 final presentation (14 Nov 2026).
- **Real use (framed):** weekly, during the July–October peak, by city health officers making allocation calls under time pressure.
- **Data flow:** a batch pipeline writes one artifact folder per run (`data/artifacts/<run_id>/`). The front end only reads it and records approval decisions.

## Capabilities and Constraints

- **The artifacts (shapes in `docs/CONTRACTS.md`):**
  - weekly forecast (`p_elevated`, count quantiles, alert level, top drivers, data-freshness dates);
  - barangay index with 4 components and rank bands, in resident and daytime modes;
  - 18 barangay polygons;
  - the weekly city panel;
  - stock plans and the audit log.
- **The tool never diagnoses, prescribes, decides eligibility, sends alerts or moves stock.** Every plan is a draft until an official approves or rejects it, and that decision is logged.
- **Synthetic stock numbers must be labelled synthetic** wherever they appear. The daytime population is a labelled scenario estimate.
- **Must run fully offline.**
- **Undecided:** final forecast model output (#7, #8 still stubs); real 2023–24 rain (#3) not yet in.

## Brand Commitments

- **Name:** Flood-to-Fever.
- **Team:** Chicken Wings.
- **Look:** the proposal PDF's look (sage, navy, coral, Montserrat, leaf motif) is **not binding**.

## Evidence on Hand

- **Real data:**
  - official Project CCHAIN on HDX (2008–2022 weekly cases for 12 cities, downscaled rain, NOAH hazard, Open Buildings, Mapbox isochrones, DOH geoportal);
  - PSA 2020/2024 population for the 18 barangays;
  - faeldon 2023 barangay polygons.
- **Real findings to show:**
  - the 2012 habagat lag (287 mm one week, 52 cases the next);
  - the four gate-affected barangays rank 1–4 in the index.
- **Absent, never fabricate:**
  - real doxycycline inventory;
  - 2023–26 case counts;
  - barangay-level case counts;
  - testimonials or endorsements.

## Product Principles

1. **Probability, not prophecy.** Show uncertainty and data freshness everywhere a number appears.
2. **A person decides.** The interface proposes and records; it never acts.
3. **Local truth beats generic risk.** The gate, the tide and the fish port are the story; generic heat maps aren't.
4. **Every synthetic or estimated number says so.**
5. **It has to work in the room.** Offline, fast, readable on a projector.

## Accessibility & Inclusion

- Tier colours must stay distinguishable for colour-vision deficiencies, and the tier is always written out too.
- Text must be readable on a projector at the back of a room.
- Motion must respect `prefers-reduced-motion`.
