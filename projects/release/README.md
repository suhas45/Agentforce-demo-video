# Release walkthrough (all tickets in one video)

Structure: intro card → one ~30 s split-screen chapter per ticket (explanation left, recording right with zoom + focus box) → end card.

Add a ticket:
1. Put the recording in `recordings/<area>/<ID>.mp4`.
2. Create `tickets/<ID>/ticket.json` (copy `tickets/E4-1/ticket.json`):
   - `lines`: 4 beats (Problem, Change, Demo, Result), each with on-screen `head` (≤7 words), `sub`, spoken `text` (+ `say` for pronunciation) and the recording `pieces` `[srcStart, srcEnd, weight]` that play under it.
   - `cam`: camera regions `{src, x, y, w}` in recording pixels (viewport is 2:1).
   - `focus`: highlight boxes `{src0, src1, x, y, w, h}`.
3. Add the ID to `release.json` → `tickets`.

Build: `FFMPEG=... python3 scripts/walk_build.py projects/release <kokoro dir>` (`--preview` for stills, `--only ID` to test one chapter).
