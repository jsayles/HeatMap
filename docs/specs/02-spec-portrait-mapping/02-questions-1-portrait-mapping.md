# 02 Questions Round 1 - Portrait Mapping

Please answer each question below (tick one or more options, or add your own notes). Add any extra context under a question.

**Current direction (open to change as we learn):**

- **Builds on spec 01:** the native app shell, launch secret and uv / Python 3.15 / Django 6.1 setup carry forward.
- **Database:** the Django database moves from SQLite to PostgreSQL + PostGIS (GeoDjango), using the Postgres.app 18 already running on this Mac. PostGIS 3.6.2 is available there.
- **Subjects:** the people being mapped are called **subjects** (renamed from "participant"). A Subject profile lives in the database, separate from Django's `User`, which is reserved for the logged-in user. Files on disk identify people only by ID (`subject_24`).
- **Out of scope:** no heat map, no session/GSR recording, and no body areas yet. The design must leave room for body areas as PostGIS regions later ("show me the torso" across all stored portraits).
- **Python 3.15 compatibility (tested 2026-10-25):** Apple Vision, MediaPipe, OpenCV, Shapely and psycopg all work. rembg / BiRefNet do not (no onnxruntime build for Python 3.15 yet).

## 1. What sets the fixed scale?

The bridge of the nose (between the eyes) lands at a fixed point on the standard grid. A fixed *scale* needs a second measurement on the body. Which one?

- [ ] (A) Body height: nose bridge to the midpoint between the ankles is always the same length on the grid
- [ ] (B) Eye distance: the distance between the eyes is always the same length
- [X] (C) Shoulder width
- [ ] (D) Nose bridge to the midpoint between the hips (torso length)
- [ ] (E) Other (describe)

**Recommended answer(s):** (A)

**Why these are recommended:**

- For full-body maps, what matters is that shoulders, hips, knees and feet line up across people. Scaling by body height lines up the whole body, top to bottom.
- (B) is very precise for faces but tiny relative to the body, so small errors in the eye points get multiplied into large errors at the feet. Head-to-body proportions also vary a lot between people.
- (C) and (D) line up the upper body well but let the legs drift. They'd be good choices if close-up or half-body portraits become common, which could be a later option.
- With (A), the body also needs to be rotated so the line from the nose bridge to the ankle midpoint is vertical. That straightens a slightly tilted phone photo.

I have a test image which is only the upper half and I don't have the model's height.  I'm not sure if "leg drift" is ging to be a problem so I'm inclined to not worry about it.  If you think it will please push back.  

## 2. What does "scrubbing" mean?

You described the flow as "upload, do some scrubbing, then map". What happens in the scrubbing step?

- [ ] (A) Review and correct the cutout: see the mask over the photo, and paint to add or erase areas the background removal got wrong (hair, gaps between arms and torso)
- [ ] (B) Review and correct the key points: drag the nose bridge and ankle points if detection got them wrong
- [ ] (C) Both (A) and (B)
- [ ] (D) Removing hidden data from the photo file (location, camera details); see question 5
- [X] (E) Something else (describe)

Both A and B are going to be required at some point but I think they are a bit beyond MVP.  I was thinking brightness/contrast or any image shapening that needed to happen but that too may be beyond the MVP.  Let's just keep it simple for now and not scrub.  But we know we'll go there in later versions.  

**Recommended answer(s):** (C), with (A) kept simple in this MVP: accept or reject the cutout, plus a basic add/erase brush

**Why these are recommended:**

- Automatic background removal and pose detection will sometimes be wrong. A human check before the portrait is saved to the map keeps bad outlines out of PostGIS, where they would quietly spoil every later "show me the X" query.
- Dragging two points (B) is cheap to build and fixes most alignment errors. A full mask editor is a bigger job, so a basic brush is enough for the MVP.

## 3. Which photos do we test and develop with?

Choosing "the best boundary" means comparing methods on real full-body photos. These photos will be used during development, and *results* may appear in proof artifacts committed to git.

- [ ] (A) Your own portraits (for example, you in the anatomical pose), kept local and never committed. Proofs show only outlines and numbers, not the photos
- [ ] (B) Openly licensed full-body photos (for example Wikimedia Commons / public-domain anatomy references) that can be committed as test fixtures
- [X] (C) Both: (B) for automated tests and committed proofs, (A) for judging the real-world boundary quality
- [X] (D) Other (describe)

**Recommended answer(s):** (C)

**Why these are recommended:**

- Automated tests need a photo that lives in the repo, so it must be openly licensed (B).
- The decision about the "best boundary" should be made on photos like the real ones: a phone camera, a home setting, skin and hair (A). Those must stay off git.
- Using only (A) means the tests can't run anywhere without your private photos. Using only (B) risks choosing a method that does well on studio stock photos but badly on phone photos.

I'll upload some anatomical photos of myself and a few agreeing subjects for the test data.  We can also use some public ones if we can find them.  

## 4. How do we pick the background-removal method?

- [X] (A) Build a side-by-side comparison first (Apple Vision person segmentation, Apple Vision foreground mask, MediaPipe image segmenter). You choose by eye from the outlines drawn over the photos; we build on the winner only
- [ ] (B) Same comparison, but keep every method available behind one switch so we can change later
- [ ] (C) Just use Apple Vision person segmentation and move on
- [ ] (D) Other (describe)

**Current best-practice context:** neither Apple nor Google publishes edge-quality comparisons for these models. Both point to testing on your own images.

**Recommended answer(s):** (A), with a one-line setting that names the method, so swapping later only means adding a new one
Agreed to your recommendation

**Why these are recommended:**

- A good boundary is your stated priority, and no published comparison exists, so a short comparison is the only honest way to choose.
- Keeping all of them working (B) means maintaining code nobody uses. A clean single interface makes adding another method later easy, for example rembg once onnxruntime supports Python 3.15.
- (C) is fastest, but it's a guess.

## 5. Remove hidden data from uploaded photos?

Phone photos usually carry hidden data: GPS location (often the subject's home), the time, and the phone model.

- [X] (A) Yes: when a photo is imported, apply its rotation, then save the copy we keep without any of this data. The original file never enters the app folder
- [ ] (B) Keep the original as-is, and remove the data only from images we create
- [ ] (C) Not needed now

**Recommended answer(s):** (A)

**Why these are recommended:**

- A nude photo plus the GPS location of someone's home is the most dangerous combination this project could hold. Removing it on import costs a few lines and means it never exists in the app.
- (B) keeps that risk sitting in the app folder (and in backups of it).
- This adds a safeguard you didn't ask for, so it's your call. I recommend it because of what these photos are.

Agreed but only the location data.  Camera data is useful.  

## 6. Which photos per subject?

- [X] (A) One front photo per subject for this MVP; the data model allows more later (back, close-ups)
- [ ] (B) Front and back photos from the start
- [ ] (C) Several photos per subject of any kind, each tagged (front, back, close-up)

**Recommended answer(s):** (A)

**Why these are recommended:**

- Alignment and the standard grid are defined for a front-facing body in the anatomical pose. A back view needs its own grid (no nose bridge visible), which deserves its own design.
- Shaping the data model as "a subject has portraits, each with a view type" keeps (B) and (C) easy later.

Yes.  B and C are later. 

## 7. What is stored, and where?

- [X] (A) Image files on disk; PostGIS stores geometry and numbers:
  - **Files:** the cleaned original, the cutout, and the aligned image, using Django's standard media-file handling, kept in the git-ignored `recordings/` folder.
  - **PostGIS:** the outline polygon and the key points (nose bridge, eyes, shoulders, hips, ankles...), in both the original-photo and standard-grid coordinates, plus the alignment numbers (shift, scale, rotation).
- [ ] (B) Like (A), but the outline is kept only in standard-grid coordinates
- [ ] (C) Store the images in the database too
- [ ] (D) Other (describe)

**Recommended answer(s):** (A)

**Why these are recommended:**

- The standard-grid copies make "show me the faces across everyone" possible later. The original-photo copies let the heat map be drawn back onto the subject's own unaltered photo, with no alignment error baked in.
- Storing the alignment numbers means either copy can always be recomputed from the other.
- Images in the database (C) bloat backups and make deleting a subject's photo harder to verify. Files on disk can be deleted and checked directly ("watch me delete it").
- Pointing Django's media folder at `recordings/` keeps everything private in the one folder that's already git-ignored, rather than adding a second one.

## 8. What happens when detection fails?

Sometimes no person is found, the pose is far from the anatomical pose, or the face is hidden.

- [ ] (A) Show a clear message saying why, and let you place the key points by hand (ties into question 2B)
- [ ] (B) Reject the photo with a message; you ask the subject for a new one
- [X] (C) Both: place points by hand when the outline is fine; reject when there's no usable outline

**Recommended answer(s):** (C)

**Why these are recommended:**

- Asking someone for a new nude photo is a real cost in trust, so the app should save a photo whenever it reasonably can (A).
- A photo with no usable outline can't be mapped at all, so rejecting it with a clear reason is more honest than producing a broken map.

Agreed.  Keep in mind I think a lot of the time people are going to be clothed too.  I'll push to have tighter clothes that show their outline but if they don't want to be nude I still want them to have a path to participate.  This means we do need to record some information on the photo like if they are fully dressed, partially dressed, or fully nude... I think we need to know if the breasts and the sex are exposed or we could have a "list of parts that are not exposed" with a checkbox.... pushes the parts list... open to suggestions.