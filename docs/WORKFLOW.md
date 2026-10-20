# Team workflow

Everything for Sprint 1 is an issue in the **Sprint 1 PoC** milestone. If it isn't an issue, it isn't in the sprint.

Nobody hands out tasks. You pick what you want, work at your own pace, and own it until it's merged. The lead reviews every PR. That's the main checkpoint.

## Ground rules

1. **Pick it, own it.** Once you claim an issue it's yours through review and merge, including the fixes reviewers ask for.
2. **P0s first.** While any `P0-demo-blocker` is still open and unclaimed, grab one of those before a P1. Nobody checks this. It's how the demo gets built.
3. **One at a time.** Finish or open a PR before claiming the next issue, so there's always something left for others.
4. **Build against contracts and fixtures, not each other.** `python -m f2f.fixtures` gives you a full fake artifact folder. You never have to wait on someone else's branch to start.
5. **Announce contract changes.** Changing a column means editing `contracts.py`, `docs/CONTRACTS.md` and `fixtures.py` in the same PR, plus a comment on every open issue that reads that artifact.
6. **Freeze on day 6 at noon.** After that, only fixes for things that break the demo get merged.

## Picking up an issue

```bash
# open P0s nobody has taken
gh issue list --milestone "Sprint 1 PoC" --label P0-demo-blocker --search "no:assignee"

# claim it
gh issue edit 12 --add-assignee @me
gh issue comment 12 --body "Taking this."
```

Manual: open the issue, click **assign yourself**, leave a short comment.

Read the issue's **Depends on** section before claiming. It says what you can start with today, what has to land before you can close, and who's waiting on you. Issues marked **Critical path** (#1 → #5 → #7 → #8 → #18) set the demo date. If you take one, keep it moving or hand it back early.

No daily status reports. Your branch and your PR show where you are.

**Stuck on someone else?** Add the `blocked` label, say what you need and @ the person who has it.

**Dropping it?** Push your branch, comment where you left off, and unassign yourself. That's fine, but say so, because an issue that looks claimed won't get picked up by anyone else.

## Branches

```
feat/<issue>-<short-name>     new behaviour          feat/14-tier-map
fix/<issue>-<short-name>      bug                    fix/31-rain-lag-leak
data/<issue>-<short-name>     data files, ingest     data/4-carina-flood-log
docs/<issue>-<short-name>     docs only              docs/18-demo-script
```

Branch off the latest `main`. Rebase, don't merge `main` into your branch.

## Pull requests

- Title follows the commit style in [CONTRIBUTING.md](../CONTRIBUTING.md). The body starts with `Closes #<issue>`.
- Keep it small. Over ~400 changed lines (excluding lockfiles and fixtures) usually means two PRs.
- UI changes need a screenshot. Model changes need the metrics table before and after.
- The lead reviews and approves. Teammates are welcome to review too.
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

## Communication

The lead posts heads-ups in the group chat: scope changes, contract changes, dry-run times. Questions about an issue go in the issue, so the answer stays with the work.

If P0s aren't landing by day 3, the lead cuts scope using the cut list in [SPRINTS.md](SPRINTS.md) instead of anyone working later.
