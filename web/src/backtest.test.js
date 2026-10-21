import { test } from 'node:test';
import assert from 'node:assert/strict';
import { scoreRow } from './backtest.js';

test('lower is better: event model behind when a baseline scores lower', () => {
  assert.deepEqual(scoreRow([0.57, 0.51, 0.5, 0.54], -1), { best: 0.5, behind: true });
});

test('higher is better: event model on top is not behind', () => {
  assert.deepEqual(scoreRow([0.64, 0, 0.21, 0.21], 1), { best: 0.64, behind: false });
});

test('missing values are skipped, and a missing event model is never "behind"', () => {
  assert.deepEqual(scoreRow([1.2, null, 0, 0.4], 1), { best: 1.2, behind: false });
  assert.deepEqual(scoreRow([null, 0.5, 0.4, null], -1), { best: 0.4, behind: false });
  assert.deepEqual(scoreRow([null, null, null, null], 1), { best: null, behind: false });
});

test('a tie with a baseline counts as best, not behind', () => {
  assert.deepEqual(scoreRow([0.5, 0.5, 0.6, 0.7], -1), { best: 0.5, behind: false });
});
