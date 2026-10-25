# 0001 Background removal: Apple Vision person segmentation

- **Date:** 2026-10-25
- **Status:** accepted, provisional (see "Open" below)
- **Decided by:** Jacob, from side-by-side comparison sheets
- **Setting:** `SEGMENTATION_METHOD = 'vision_person'` in `heatmap/settings.py`

## Decision

Use **Apple Vision person segmentation** (`VNGeneratePersonSegmentationRequest`, quality level "accurate") to cut the body out of each portrait.

Keep **MediaPipe** (`selfie_multiclass_256x256`) in `body_map/segmentation.py` as the cross-platform fallback. Switching is one setting.

## Candidates

| Method | Platform | Notes |
| --- | --- | --- |
| `vision_person`: Apple Vision person segmentation | macOS only | Built for people. Best boundary overall. |
| `vision_foreground`: Apple Vision foreground instance mask | macOS 14+ only | General "prominent subject" mask. Close second, slightly softer edges. |
| `mediapipe`: MediaPipe selfie multiclass segmenter | Cross-platform | Picked up a second person and stray fragments in busy scenes. |
| rembg / BiRefNet | Cross-platform | Not tested: they need onnxruntime, which has no Python 3.15 build yet. |

## How it was judged

`uv run manage.py compare_segmentation tests/fixtures/images` drew each method's outline over each photo, side by side. Jacob compared:
- Edges on hair.
- The gaps between arms and torso.
- Skin against the background.
- Anything wrongly included or cut off.

**Photos:** the 10 openly licensed fixtures in `tests/fixtures/images/` (credits in `ATTRIBUTION.md`):
- **Coverage:** 4 nude, 2 partly clothed, 4 clothed.
- **Framing:** 8 full body, 2 upper body.
- **Backgrounds:** plain studio, busy street and dance studio, dark backdrop, open water.
- **Hard cases included:** long loose hair, arms close to the torso, a bicycle in front of the body, and a mirror with a second person.

**Run time:** about 0.1–0.5 s per photo for every method on this laptop.

## What was seen

- `vision_person` gave the cleanest, tightest boundary overall, including on long hair and arm/torso gaps. In the busy dance studio it outlined only the dancer.
- **Sheet 07** (standing in open water) is the hardest case. `vision_person` cuts into one thigh and runs the outline down into the water below the knee. This is the kind of error the future mask-editing ("scrubbing") step should correct.
- `mediapipe` included the second person in the mirror scene, plus stray fragments of the background.

## Why

- The boundary is the priority, and `vision_person` was best on the evidence available.
- Everything it produces (the mask, then the outline polygon in PostGIS) is plain, platform-independent data. Only this processing step is macOS-specific, so moving platforms later means changing one setting, not the data.

## Open

- **Not yet tested on private portraits.** The spec's goal of judging on at least 5 real phone portraits (yours and consenting subjects') was not met; this choice rests on the openly licensed fixtures only. Re-run `compare_segmentation` on real portraits, kept in a folder inside `recordings/`, before relying on it for real sessions.
- **Cross-platform preference:** Jacob would prefer not to depend on Apple. Revisit when rembg / BiRefNet run on Python 3.15, or if the app needs to run off macOS.
- **Landmarks:** the spec said to use the winning framework's detector for key points. Because of the cross-platform preference, task 5.0 should consider MediaPipe landmarks instead: 33 body points and an exact nose-bridge point (face mesh #168), versus Apple Vision's 19 joints.
