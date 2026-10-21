---
name: Flood-to-Fever
description: Leptospirosis early warning and decision support for Navotas City, read as stacks of banyera crates on poured concrete.
colors:
  ground: "#e4e5e1"
  ice: "#f7f8f5"
  paper: "#ffffff"
  banyera-blue: "#1f4fbf"
  banyera-deep: "#163a8f"
  crate-face: "#2f68e6"
  ink: "#14213a"
  mute: "#4f5a6e"
  rail-text: "#dbe4fa"
  line: "#c9cbc4"
  soft: "#dcded8"
  row-hover: "#eef0eb"
  row-selected: "#e3e9f7"
  sodium-amber: "#f2a33a"
  watch-text: "#9a5a0a"
  marker-red: "#d6322b"
  red-text: "#b3241e"
  sky: "#86c5e8"
  waterline: "#2f7fb8"
  standby: "#aeb4bd"
  plate: "#cfd1ca"
typography:
  display:
    fontFamily: "Barlow Condensed, sans-serif"
    fontSize: "60px"
    fontWeight: 600
    lineHeight: 1
    fontFeature: "tnum"
  headline:
    fontFamily: "Barlow Condensed, sans-serif"
    fontSize: "28px"
    fontWeight: 600
    lineHeight: 1
    fontFeature: "tnum"
  numeral:
    fontFamily: "Barlow Condensed, sans-serif"
    fontSize: "20px"
    fontWeight: 600
    fontFeature: "tnum"
  title:
    fontFamily: "Barlow, sans-serif"
    fontSize: "17px"
    fontWeight: 700
  body:
    fontFamily: "Barlow, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.4
    fontFeature: "tnum"
  label:
    fontFamily: "Barlow, sans-serif"
    fontSize: "12px"
    fontWeight: 700
    letterSpacing: "0.08em"
  caption:
    fontFamily: "Barlow, sans-serif"
    fontSize: "12px"
    fontWeight: 500
rounded:
  tag: "2px"
  control: "3px"
  panel: "4px"
spacing:
  xs: "6px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "24px"
components:
  button:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    typography: "{typography.caption}"
    rounded: "{rounded.control}"
    padding: "5px 12px"
  button-hover:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
  button-primary:
    backgroundColor: "{colors.banyera-blue}"
    textColor: "{colors.paper}"
    rounded: "{rounded.control}"
    padding: "5px 12px"
  button-primary-hover:
    backgroundColor: "{colors.banyera-deep}"
  segment-on:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
    padding: "5px 12px"
  chip:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "4px 10px"
  panel:
    backgroundColor: "{colors.ice}"
    rounded: "{rounded.panel}"
  panel-header:
    height: "48px"
    padding: "6px 16px"
  tag-warning:
    backgroundColor: "{colors.marker-red}"
    textColor: "{colors.paper}"
    rounded: "{rounded.tag}"
    padding: "1px 5px"
  tag-watch:
    backgroundColor: "{colors.watch-text}"
    textColor: "{colors.paper}"
    rounded: "{rounded.tag}"
    padding: "1px 5px"
  nav-item:
    textColor: "{colors.rail-text}"
    rounded: "{rounded.panel}"
    width: "60px"
    height: "58px"
  nav-item-active:
    backgroundColor: "{colors.ice}"
    textColor: "{colors.banyera-blue}"
  table-row:
    height: "44px"
    padding: "0 16px"
  table-row-selected:
    backgroundColor: "{colors.row-selected}"
---

# Design System: Flood-to-Fever

## Overview

**Creative North Star: "Bulungan at Dawn"**

The dashboard reads Navotas the way the fish port reads its morning. Each barangay is a stack of blue banyera crates on a poured-concrete ground. Stack height is priority, and flood water rises around the stacks as the replay runs. The 3D crate city is the main working surface. It is not decoration around a KPI grid.

Around the city, the DOM side is an operations console. It is matte and dense, with squared 3-4px corners, 1px rules, and one strict grid. Every count is set in condensed tabular numerals. Every number has its source and date beside it. Colour is reserved for state: blue is the world's material (the shell rail and every crate), and amber, red and sky carry the three alert tiers. The line itself carries data quality. A solid line is observed and a dashed line is synthetic, estimated or not yet observed.

Motion is part of the data. One replay timeline drives the water, the crate re-stacks and the alert colours, all with an exponential ease-out. Nothing moves unless the data changed or the user selected something.

**Key Characteristics:**
- Concrete ground, ice-white panels, banyera-blue shell and crates.
- Condensed tabular numerals for every count, regular Barlow for everything else.
- Line form carries data quality: solid for observed, dashed for synthetic or estimated.
- Source and date beside every number.
- Selection lifts one item and dims the rest, in the map and the table at the same time.
- Flat DOM; the only shadows come from the dawn sun in the 3D scene.

## Colors

A cool concrete-and-ice neutral field, one committed material blue, and three tier colours that appear only when there is something to say.

### Primary
- **Banyera Blue** (banyera-blue): The material of the world. Fills the 72px shell rail, the primary button, the rain bars, the stock capacity block, the stamp and the rib colour of every crate. Hovered primary buttons go to **Banyera Deep** (banyera-deep), which is also the crate edge stroke.
- **Crate Face** (crate-face): The lighter polymer blue of the crate sides in the 3D scene. Used only in the crate texture.

### Secondary
- **Marker Red** (marker-red): Act now and warning. Fills crate lids of act-now stacks, rank badges on map labels, WARNING tags, the warning rain line, rank-band fills and the stock spill hatch. **Red Text** (red-text) is the same meaning set as text: ranks, warning percentages and unmet figures.
- **Sodium Amber** (sodium-amber): Prepare and watch. Fills prepare crate lids, the stale-data dot on chips and the gate-impaired dot. **Watch Text** (watch-text) is the deep amber used for any watch text, the WATCH tag and the watch rain line.
- **Sky** (sky): Monitor tier and flood water. Monitor crate lids, the translucent water slabs (55% opacity) and the arrow in the F→F wordmark. The hard edge of each water slab is **Waterline** (waterline).

### Neutral
- **Poured Concrete** (ground): Page and 3D scene background.
- **Ice** (ice): Panel surface, active nav item and the slider thumb border.
- **Paper** (paper): Fill for controls, chips, map labels and notes that sit on top of a panel or the scene.
- **Ink** (ink): All primary text, control borders, label leaders, the slider and the "now" line on the rain chart.
- **Mute** (mute): Source lines, column headers, ticks and secondary captions.
- **Line** (line): Panel borders, the top-bar rule, select borders and the empty slider track.
- **Soft** (soft): Rules inside panels: header bottoms, table rows, forecast column dividers, empty rank-band tracks.
- **Row Hover / Row Selected** (row-hover, row-selected): Table row states. Selected rows take a faint blue tint.
- **Standby** (standby): Crate lids and the legend swatch when no forecast week is on alert.
- **Plate** (plate): The extruded barangay ground plates in the 3D scene.
- **Rail Text** (rail-text): Nav labels and icons on the blue rail.

### Named Rules
**The Tier Colour Rule.** Red, amber and sky mean act now, prepare and monitor. Use them for nothing else. The tier is always written in text too (legend, tag, table), never shown by colour alone.

**The Fill-Versus-Text Rule.** Marker red and sodium amber are fill colours. Text, thin lines and tags that carry those meanings use red-text and watch-text, which keep legible contrast on ice and paper.

**The Standby Rule.** The priority index is always standing, but tier colours and act-now labels appear only while a forecast week is on watch or warning. Otherwise crate lids go standby grey and the act-now table drops to 55% opacity.

## Typography

**Display Font:** Barlow Condensed (sans-serif fallback), weights 600 and 700, self-hosted via @fontsource.
**Body Font:** Barlow (sans-serif fallback), weights 400, 500, 600 and 700, self-hosted via @fontsource.

**Character:** Barlow is a plain, slightly industrial grotesque that holds up on a projector. Barlow Condensed is reserved for numbers, so counts look like they were stencilled on the port's whiteboard and stay narrow enough to sit in dense columns.

### Hierarchy
- **Display** (600, 60px, line-height 1; 44px under 640px): Forecast probabilities for weeks +1 to +3. Coloured by alert level.
- **Headline** (600, 28px, line-height 1): Stock figures (on hand, need, unmet).
- **Numeral** (600-700, 20-22px): Table scores and ranks, the current replay date, the wordmark.
- **Title** (700, 17px): The page title in the top bar. One per page.
- **Body** (400-500, 14px, line-height 1.4): Table cells and general text. The body sets `font-variant-numeric: tabular-nums` globally.
- **Label** (700, 12px, 0.08em tracking, uppercase): Panel headings (h2) only.
- **Caption** (500-600, 11-12px): Buttons, chips, legend, source lines, ticks, column headers and nav labels.

### Named Rules
**The Condensed Count Rule.** Every count, probability, score, rank and date readout is Barlow Condensed with tabular figures. Words are never set in the condensed face, except the approval stamp and the F→F wordmark.

**The Eleven Pixel Floor Rule.** Nothing is set below 11px. The room reads this on a projector.

## Layout

The shell is a CSS grid with a fixed 72px blue rail and a fluid main column. The main column has a 56px top bar (title, freshness chips, run id) above the working grid. The working grid has a 16px gap and 16px 24px 12px padding. It uses two columns: the crate city on the left, minmax(0, 1fr), and a fixed 480px right column. It has two rows: the map row, at least 520px tall, and an auto-height bottom row. The right column stacks the forecast panel above the act-now table. The bottom row places the replay scrubber under the map and the stock strip under the right column.

At 1180px and below, the working grid collapses to one column and the top bar wraps. At 640px and below, the rail becomes a horizontal bar above the content, page padding drops to 12px, the forecast numerals drop to 44px, and map labels show only their rank badge. The barangay name stays in the table.

Spacing runs on 6, 8, 12, 16 and 24px. 16px is the panel inset and grid gap. 12px is the gap between tightly related controls. 24px is the top bar's side padding. Panel headers are at least 48px tall. Legends and table rows are 44px, so every row stays a usable touch target.

**The One Grid Rule.** All panels sit on the single working grid and align to its gutters. Panels do not float, overlap or nest panels inside panels.

## Elevation & Depth

The DOM is flat. No element uses `box-shadow`. Panels are separated from the concrete ground by tone (ice on concrete) and a 1px line border. Overlays on the scene (map labels, the WebGL fallback note) are paper boxes with a 1px ink border.

Real depth exists only inside the 3D scene. A hemisphere light and one low, warm directional "dawn sun" (#fff1d9) from the bay side cast contact shadows from the crate stacks onto the concrete plates. The camera is orthographic, so stack heights compare honestly across the strip.

### Named Rules
**The Only Shadow Is the Sun Rule.** Depth in the DOM comes from tone and 1px rules. Shadows exist only in the 3D scene, cast by the single dawn light.

**The No Glow Rule.** No glow, no glass, no blur, no smooth colour gradients. Hard-stop gradients that draw a flat fill (the slider progress) or the 135-degree overflow hatch are part of the system.

## Shapes

Corners are squared off: 4px on panels and nav items, 3px on buttons, chips, selects, segmented controls and the stamp, and 2px on tags and the slider thumb. Map labels, legend swatches, rank-band tracks and the stock strip have no radius at all. The only circles are 8px status dots.

Borders are 1px. Ink borders mark interactive or overlay elements (buttons, chips, segmented control, map labels). Line and soft borders mark structure. The 2px border is reserved for emphasis: the stock capacity block, the break mark on a truncated spill and the stamp.

The line form carries data quality. A dashed bottom border marks synthetic or estimated text, and a dashed outline marks a synthetic chip or swatch. A dashed outline also marks a not-yet-observed rain bar, and a dashed empty track marks a rank band that is pending. The same element drawn solid is observed.

**The Solid-Means-Observed Rule.** Draw observed data with solid lines and fills. Draw synthetic, illustrative, estimated or pending data with a dashed line of the same colour. Never use dashing as decoration.

## Components

### Buttons
Squared and plain. They look like hardware switches, not pills.
- **Shape:** slightly squared (3px), 1px ink border, 12px/600 caption text.
- **Default:** paper fill, ink text. Hover inverts to ink fill and paper text over 150ms.
- **Primary:** banyera-blue fill and border, paper text. Hover goes to banyera-deep. There is one primary action per group (Play, Approve plan).
- **Disabled:** 50% opacity, not-allowed cursor.
- **Focus:** the global 2px ink outline at a 2px offset.

### Segmented Control
A row of plain buttons inside one 1px ink border with ink dividers. The checked option inverts to ink fill and paper text. Built as a radiogroup with `aria-checked` (Residents / Daytime).

### Chips
Freshness facts in the top bar.
- **Style:** paper fill, 1px ink border, 3px radius, 12px/500 text, with an 8px status dot in front.
- **State:** a blue dot means current. An amber dot means stale. A dashed border means the data is illustrative.

### Panels
- **Corner Style:** 4px.
- **Background:** ice, with a 1px line border on the concrete ground.
- **Header:** at least 48px tall, 16px side padding, soft bottom rule. It holds an uppercase label heading, then a mute source line, then right-aligned controls.
- **Internal Padding:** 16px sides. Content rhythm uses 12-16px.

### Inputs / Fields
- **Backtest table:** one row per metric with a 'lower/higher is better' caption, one column per model, the event model's column tinted blue. The best value in a row gets a 2px ink outline; where a baseline beats the event model, its cell carries a red 'behind' caption. The sentence above the table is assembled from the scores, never typed.
- **Text field:** paper fill, 1px line border, 3px radius, 13px text, 2px ink focus ring.
- **Scenario control:** a segmented control of equal buttons with a 1px ink frame; each button holds a 12px label and a 15px condensed figure.
- **Replay scrubber:** a 4px track with ink progress over the line colour. The thumb is a 14x22px ink block with a 2px ice border and a 2px radius. Tick dates sit below in 11px mute.

### Navigation
A 72px banyera-blue rail with the F→F wordmark at the top. Items are 60x58px with a 20px stroked SVG icon (stroke-width 1.8) over an 11px/600 label in rail-text. The active item is an ice tile with blue text. Destinations that are not built yet stay visible, are marked `aria-disabled`, are dimmed, and give the reason in a title tooltip. Under 640px the rail becomes a horizontal bar.

### Crate City (signature)
The main surface. It is a three.js orthographic scene of the 18 barangay plates extruded on concrete. On each plate is a stack of 1 to 8 banyera crates, and stack height is the rounded priority score. The top crate's lid carries the tier colour, or standby grey. Act-now stacks get a paper label with a red condensed rank badge and an ink leader line. Neighbouring labels alternate leader height and side so leaders never cross. Place names (Manila Bay, Malabon) are 11px/600 uppercase with 0.18em tracking, set straight on the ground.
- **Replay:** scrubbing or Play raises each barangay's water slab in proportion to its hazard (1.4s) and re-stacks the crates one crate at a time (0.7s, staggered 40ms).
- **Selection:** clicking a stack or a table row lifts that stack 1.4 units (0.6s). All other stacks, labels and table rows dim (labels to 25%, rows to 45%). Clicking the same item again clears the selection.
- **Controls:** orbit is limited to plus or minus 0.6 rad of azimuth and 30-66 degrees of polar angle. Pan is off. Zoom is limited to 0.8-3x.

### Forecast Cell
Three columns split by soft rules. Each column has a mute "Week +n" line with either a WARNING/WATCH tag or the target date. Below that is the 60px condensed probability, coloured red-text, watch-text or ink by alert level, with a dashed underline while the forecast is synthetic. At the bottom is a 22px history sparkline of 7px bars, with the current week in the alert colour.

### Act-Now Table
40px rows with soft rules. The rank is a 20px/700 condensed numeral in red-text. The score is a right-aligned 20px condensed numeral. The rank band is a 96px soft track with a red span for the p05-p95 interval. While bands are pending, it shows a dashed empty box and the word "pending" with a dashed underline. Rows are focusable and select on Enter or Space.

### Stock Strip
Three condensed headline figures, with unmet in red-text. Below them is a fixed-width capacity block: banyera-blue with a 2px ink border, set at 34% of the strip. The unmet amount spills to its right as a red 135-degree hatch. When the spill is too long to draw, it gets a skewed ice break mark with ink edges, and the overflow ratio is written in the unmet caption ("unmet · 14.6× on hand"). Under the strip, the three uptake scenarios sit side by side as a segmented control: each button names its uptake and its unmet figure in red-text condensed, and the selected one is ink with paper text. Below that, one row: an "Official" text field, then Approve and Reject, both disabled until a name is typed and while a request is in flight. Decisions are recorded by the local Python server; the page only shows what the audit log says. After a decision the row is replaced by a stamp: 15px/700 condensed uppercase with 0.06em tracking, a 2px border, blue for approved and red-text for rejected.

## Do's and Don'ts

### Do:
- **Do** set every count, probability, score, rank and readout date in Barlow Condensed with tabular figures.
- **Do** put a mute source line (source, model or scenario, and date) in every panel header that shows a number.
- **Do** draw synthetic, illustrative, estimated or pending data with a dashed line, and observed data solid.
- **Do** use marker red and sodium amber as fills only; use red-text (#b3241e) and watch-text (#9a5a0a) for text and thin lines with those meanings.
- **Do** write the tier out in text wherever its colour appears.
- **Do** dim everything except the selection, in the map and the table together, when an item is selected.
- **Do** animate only data changes and selection, with expo.out easing, and set every duration to zero under `prefers-reduced-motion`.
- **Do** keep icons as inline stroked SVG (stroke-width 1.8, round joins), and bundle every font and script locally so the page runs offline.

### Don't:
- **Don't** use `box-shadow`, glow, glass, blur or smooth colour gradients on DOM surfaces.
- **Don't** use red, amber or sky for anything except the act-now, prepare and monitor tiers (sky also draws flood water).
- **Don't** round corners past 4px or use pill shapes; circles are reserved for 8px status dots.
- **Don't** use dashed lines as decoration; a dash always means the data is not observed.
- **Don't** set words in Barlow Condensed, except the approval stamp and the F→F wordmark.
- **Don't** show a number without its source and date nearby.
- **Don't** fall back to a KPI-card grid around a flat choropleth; the crate city is the main surface.
