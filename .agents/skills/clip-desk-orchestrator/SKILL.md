---
name: clip-desk-orchestrator
description: Master orchestrator for the complete GTA 6 clipping desk workflow: trend/stream discovery, moment detection, clip generation, hook writing, campaign-rule verification, and human approval.
---

# GTA 6 Clip Desk Master Orchestrator

This skill coordinates the full end-to-end pipeline from discovering trends to generating fully captioned, campaign-compliant vertical clips ready for human approval.

## Pipeline Overview

```text
[1. Discovery] ──> [2. Moments] ──> [3. Hook & Layout] ──> [4. Clip Cut] ──> [5. Rule Check] ──> [6. Human Gate]
 trends.py          moments.py       hook-writer            cut.py           check.py          User "Yes"
 streams.py
```

---

## Step-by-Step Orchestration Protocol

### Stage 1: Discovery (Trends & Streams)
1. Check for live clipping campaigns:
   - Review `campaigns.md`. If empty or outdated, use `campaign-finder`.
2. Discover trending videos or live streams:
   - For trending YouTube uploads:
     ```bash
     python scripts/trends.py --query "gta 6" --hours 24 --limit 30
     ```
   - For active live streams (YouTube & Twitch):
     ```bash
     python scripts/streams.py --query "gta 6" --limit 20
     ```
3. Filter out leaks, piracy, exploits, and "play early" fake content. Select 1 high-potential target video.

---

### Stage 2: Moment Detection
1. Analyze the selected video or VOD:
   ```bash
   python scripts/moments.py "<VIDEO_URL_OR_FILE>" --top 8
   ```
2. The script outputs:
   - `jobs/<id>/candidates.md`
   - `jobs/<id>/candidates.json`
   - `jobs/<id>/transcript.json`
3. Review the candidate list scored by loudness spikes, transcript hype words, heatmap, and chat activity.
4. Select the best moment (`pick` number 1 to 8).

---

### Stage 3: Hook & Layout Selection
1. **Hook Writing**: Generate 3 hook options following the `hook-writer` guidelines (sentence case, 3 to 9 words, verified facts only):
   - Option A (Situation): *"When the cops chase the wrong player"*
   - Option B (Negation / Difference): *"You can't do this in GTA 5"*
   - Option C (Number promise): *"3 things you missed in this chase"*
   Select the strongest hook.
2. **Layout Selection**:
   - `fill`: Standard vertical crop (best for pure gameplay).
   - `blur`: Full 16:9 frame centered over blurred background (best when cropping cuts action).
   - `facecam` / `react`: Streamer webcam on top, gameplay below (best for reactions).

---

### Stage 4: Clip Generation
1. Cut the clip with word-by-word burned captions and hook overlay:
   ```bash
   python scripts/cut.py jobs/<id> --pick <PICK_NUM> --layout <LAYOUT> --hook "<SELECTED_HOOK>"
   ```
2. For streamer reaction clips:
   ```bash
   python scripts/cut.py jobs/<id> --pick <PICK_NUM> --layout react --cam auto --title "<REACTION_TITLE>" --title-style box --captions bubble
   ```
3. Verify output in `jobs/<id>/edits/clip_<PICK_NUM>.mp4`.

---

### Stage 5: Rule & Campaign Check
1. Validate against technical specs, platform rules, and campaign requirements:
   ```bash
   python scripts/check.py jobs/<id>/edits/clip_<PICK_NUM>.mp4 --campaign campaigns.md --caption "<DRAFT_CAPTION>"
   ```
2. Ensure:
   - Resolution is exactly 1080x1920, 30 fps, audio present.
   - Duration is within campaign limits (typically 15-60s).
   - Zero banned buzzwords ("leak", "glitch", "free download").
   - Required hashtags and creator mention/credit (`🎥 @creator`) are present in caption.
3. If check fails, fix the parameter and re-cut until `RESULT: PASS`.

---

### Stage 6: Mandatory Human Approval Gate
> [!CRITICAL]
> **NEVER POST OR UPLOAD AUTOMATICALLY.**

Present the final package to the user in a single structured message:
1. **Clip File Link**: `jobs/<id>/edits/clip_<PICK_NUM>.mp4`
2. **Duration & Specs**: `XX.X seconds`, 1080x1920, -14 LUFS.
3. **Selected Hook**: `"<HOOK_TEXT>"`
4. **Draft Caption & Credit**:
   ```text
   [Hook line]
   
   [1-2 sentence context or tip]
   
   🎥 @[CreatorHandle]
   #GTA6 #GTAVI
   ```
5. **Verification**: Confirm all automated checks passed.

Wait for the human's explicit approval ("Yes") before marking the task complete. The human posts the clip manually.
