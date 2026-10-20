# Team workflow

Everything for Sprint 1 is an issue in the **Sprint 1 PoC** milestone. If it isn't an issue, it isn't in the sprint.

## Ground rules

These exist so the demo doesn't depend on luck.

1. **One issue in progress per person.** Claim a second one only after the first has an open PR.
2. **P0 before P1.** While any `P0-demo-blocker` is unclaimed, nobody starts a P1. End of day 1, the lead assigns any P0 still unclaimed.
3. **Claims expire.** No commit, push or comment for 24 hours and the issue is fair game. Ask in the issue, wait 2 hours, then the lead reassigns.
4. **Lanes have owners.** Anyone can take any issue, but each lane has one person who makes sure its P0s land. The lane owner isn't the only one working there.

   | Lane | Covers | Owner |
   |---|---|---|
   | A | data ingest, panel, flood log | |
   | B | baselines, event model, replay | |
   | C | crosswalk, index, exposure, planner | |
   | D | dashboard | |
   | E | demo script, requests, deck | |

5. **Build against contracts and fixtures, not each other.** `python -m f2f.fixtures` gives you a full fake artifact folder. Nobody waits on another branch to start.
6. **Contract changes are announced.** Changing a column means editing `contracts.py`, `docs/CONTRACTS.md` and `fixtures.py` in the same PR, plus a comment on every open issue that reads that artifact.
7. **Freeze on day 6 at noon.** After that, only fixes for things that break the demo get merged.

## Picking up an issue

```bash
# open P0s nobody has taken
gh issue list --milestone "Sprint 1 PoC" --label P0-demo-blocker --search "no:assignee"

# claim it
gh issue edit 12 --add-assignee @me
gh issue comment 12 --body "Taking this. Expect a PR by Thursday."
```

Manual: open the issue, click **assign yourself**, leave a one-line comment with when you expect a PR.

**Daily update**, one comment on your issue before standup:

```
done: CHIRPS pull works for 2015-2020
next: 2021-2024, then the overlap plot
blocked: no
```

**Stuck?** Add the `blocked` label, say what you need and @ the person who has it. Don't sit on it for half a day.

**Dropping it?** Push your branch, comment where you left off, unassign yourself. That's fine. Ghosting an issue isn't.

## Branches

```
feat/<issue>-<short-name>     new behaviour          feat/14-tier-map
fix/<issue>-<short-name>      bug                    fix/31-rain-lag-leak
data/<issue>-<short-name>     data files, ingest     data/4-carina-flood-log
docs/<issue>-<short-name>     docs only              docs/19-demo-script
```

Branch off the latest `main`. Rebase, don't merge `main` into your branch.

## Pull requests

- Title follows the commit style in [CONTRIBUTING.md](../CONTRIBUTING.md). The body starts with `Closes #<issue>`.
- Keep it small. Over ~400 changed lines (excluding lockfiles and fixtures) usually means two PRs.
- UI changes need a screenshot. Model changes need the metrics table before and after.
- One approval, from anyone. Reviewers respond within about 4 hours during the sprint.
- The author squash-merges after approval and deletes the branch.
- Nothing merges to `main` in the 2 hours before a dry run without the lead's OK.

## Definition of Done

Check all of these before opening the PR:

- [ ] Every acceptance criterion in the issue is met.
- [ ] `pytest -q` passes locally.
- [ ] New logic has a test. UI has a screenshot.
- [ ] Artifact outputs go through `contracts.check`.
- [ ] Contract changed → `contracts.py`, `docs/CONTRACTS.md` and `fixtures.py` updated together.
- [ ] No `data/`, `CONFIDENTIAL/`, `.env` or notebook outputs staged.
- [ ] Anything synthetic says so on screen.
- [ ] Rebased on `main`.

## Standup

15 minutes, same time every day. Each person gives their issue number, what's done, what's next and whether they're blocked. The lead closes with the count of P0s open, claimed and merged. If that count isn't moving by day 3, we cut scope (see the cut list in [SPRINTS.md](SPRINTS.md)) instead of working later.
