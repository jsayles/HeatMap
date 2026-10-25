# 02 Questions Round 2 - Portrait Mapping

Two follow-ups from your round 1 answers.

**Settled in round 1:**

- **Scale and rotation:** the nose bridge sits at a fixed point, scale comes from shoulder width, and rotation from the shoulder line. Upper-body-only photos are fine.
- **No scrubbing in the MVP:** no mask editing and no brightness/contrast. Both come in later versions.
- **Test photos:** test photos are yours and those of consenting subjects, kept local and never committed. Openly licensed photos are used for automated tests if suitable ones can be found.
- **Background removal:** a side-by-side comparison picks one winner, behind a single setting.
- **Location data:** location (GPS) is removed on import; camera details are kept.
- **Photos per subject:** one front photo per subject, with a data model that allows more later.
- **Storage:** files go in `recordings/` using Django's media handling. Geometry, key points and alignment numbers go in PostGIS, in both original-photo and grid coordinates.

## 1. Detection fails but the outline is fine: what now?

In round 1 you chose "no scrubbing in the MVP" (Q2) and also "place points by hand when the outline is fine" (Q8C). Placing points by hand *is* a small piece of scrubbing, so the two answers conflict. Which do you want for the MVP?

- [ ] (A) Minimal hand placement only for this case: if the nose bridge or either shoulder isn't found, you click those three points on the photo. Nothing else is editable
- [X] (B) No hand placement yet: the photo is saved with its outline but marked "not aligned" with the reason. Aligning it waits for the scrubbing version
- [ ] (C) Reject the photo with a clear reason (closest to "no scrubbing")

**Recommended answer(s):** (B)

**Why these are recommended:**

- (B) keeps your "no scrubbing yet" decision and still never throws away a photo someone trusted you with. The outline is stored, and alignment can be finished once point editing exists.
- (A) is small, but it is the start of the editing screen you've deferred. Fine if you want it now.
- (C) costs a subject's trust for what may just be a hidden eye or a turned head.

Fine for MVP but we'll come back to this soon after. Agree because skipping the edit page keeps the MVP minimal. 

## 2. Recording what the photo shows (coverage)

You want to record how much a photo shows (fully dressed, partly dressed, nude), and whether specific areas such as the breasts and genitals are exposed. Your notes also tie this to the reciprocal catalog: "you see what you've shared."

- [ ] (A) One overall level only: clothed / partly clothed / nude
- [X] (B) A short, fixed list of **exposure areas**, each ticked if exposed: chest/breasts, genitals, buttocks. The overall level is worked out from the ticks (none → clothed, some → partly, all visible → nude)
- [ ] (C) Use the full body-parts list with an "exposed" tick per part (needs the parts list now)
- [ ] (D) Other (describe)

**Recommended answer(s):** (B), stored so that each exposure area can later be linked to a body area in the parts catalog

**Why these are recommended:**

- The reciprocal-catalog rule, and anything about what a subject agrees to show, depends on these few areas, not on knees or elbows. A short list covers the decision that matters without building the parts catalog yet.
- Working out the overall level from the ticks avoids contradictions (for example "nude" with nothing ticked). Saving the level separately as well would allow that.
- (A) is too coarse: topless and fully nude are very different trust steps.
- (C) pulls the whole parts catalog into this MVP, which you've placed "down the line".
- **Wording:** the area names can use clinical, inclusive terms. "Genitals" covers vulva and penis, as in your notes on the Sex region. Edit the list if you'd like different areas or names.
- The ticks can be set by you at upload, and later confirmed with the subject. For the MVP, you set them.

Can we say "sex" vs "genitals"?  Feels a little less weird.  Open to push back.

