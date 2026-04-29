# Known Issues

## Timefilter timestamp timezone mismatch

**Status:** Open  
**Affected:** `filterAndSortData` in `js/utils.js`

Event `TargetProcessCreationTime` values arrive in JS as strings without a timezone suffix (e.g. `"2026-04-24T06:54:04.103188"`), so `new Date(...)` parses them as **local time**. The timefilter brush emits bounds via `Date.toISOString()` which is always **UTC** (e.g. `"2026-04-24T04:54:04.103Z"` on a UTC+2 machine). On machines with a non-zero UTC offset this causes nodes near the brush edge to be incorrectly included or excluded.

**Fix:** Normalize both sides to UTC before comparing — either append `Z` to event timestamps when serializing from Python, or parse them explicitly as UTC in JS.
