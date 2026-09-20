# Fireship-first topic research for the automatic buffer

Owner-selected reference channel:
**https://www.youtube.com/@Fireship/videos**

Run this research at the start of each automatic buffer episode, before picking
a topic or writing a script. Use the channel for timely subject discovery and
study its accessible examples of concise, engaging technical explanation. The
deliverable remains an original Richard 16:9, 3–8-minute teaching video using
the workspace's animation references and the owner's selected narration voice.

## 1. Check recent Fireship uploads first

- Open the channel's Videos page and inspect its latest accessible uploads.
  Aim to review the most recent 10–15 titles, prioritizing the last 30 days;
  record the actual number and dates available rather than inventing them.
- Record title, video URL, upload date, and topic. Include view counts only if
  actually retrieved, together with the retrieval time. A view count alone is
  not evidence that a subject is trending now.
- For relevant candidates, inspect the video description and linked sources.
  Where a transcript or playable video is accessible, study its hook, central
  question, explanation structure and visual treatment. Distinguish title-only,
  description, transcript and audiovisual inspection in the research record.
- Use available web/browser tools, a public feed, or a documented read-only
  YouTube API path when needed. Never claim to have watched a video when only
  its metadata was available. Do not expose channel OAuth credentials to the
  agent or modify subscriptions, playlists or other YouTube state for research.
- If the page is inaccessible, try a public channel feed or targeted web search
  for recent Fireship uploads. Record failures and retrieval dates. Continue
  with verified current tech sources when channel access remains unavailable;
  explicitly mark the Fireship step unavailable, not completed successfully.

## 2. Search current trends after the channel check

Build a shortlist of 3–5 candidate questions inspired by the recent subjects,
then research their current relevance independently:

- Official product announcements, release notes, engineering posts, papers,
  standards and original repositories establish what actually changed.
- Recent developer discussion, reputable tech reporting, GitHub activity or
  public trend data can corroborate interest. Record dates and URLs; do not
  label something trending merely because it has a recent article.
- Prefer a concrete development within 7–14 days when available; broaden to
  30 days or a useful evergreen mechanism if current evidence is weak.
- For a trend claim, seek one primary source supporting the technical facts
  and one independently dated signal of current interest. If that evidence is
  missing, label the topic evergreen or emerging rather than asserting a trend.

Turn a broad news topic into a teachable mechanism: how requests travel, why a
design changes cost/latency/reliability, what a tool actually does, or where a
new model fits in a software architecture. Cover relevant AI/developer tools,
databases, distributed systems, networking, cloud and DevOps subjects.

## 3. Deduplicate and choose Richard's angle

Compare candidates against `history.json`, including completed, queued,
in-progress and failed attempts, plus `topics.json`. Reject the same lesson
under a different title. A significant new release can justify revisiting a
topic only when the new mechanism/question is explicit.

Rank qualitatively by:
1. Recency and strength of trend evidence.
2. Relevance to the audience and technical teaching scope.
3. Novelty relative to this channel's history.
4. Availability of trustworthy sources and visual demonstrations.
5. Whether one complete journey, failure/recovery and tradeoff fit 3–8 minutes.

Choose one candidate with a short explanation. Seeds in topics.json are fallback
ideas, not a substitute for this first-channel-check → trend-search sequence.

## 4. Learn the format; write an original explanation

Use observed editorial techniques that serve the chosen lesson: an immediate
specific hook, concise explanation, concrete stakes, energetic pacing, visual
cause-and-effect and a useful takeaway. Record which techniques were actually
observed and how Richard will adapt them.

Write a new script from verified primary sources with a new everyday analogy,
examples, diagrams and title/thumbnail. Explain the same topic when useful,
but do not transcribe or lightly rewrite Fireship's script, reuse its footage,
audio, jokes or thumbnails, or imitate its narrator's identity. Preserve
Richard's original artwork, selected voice, light palette, sparse stage,
narration-led animations and comprehension holds. Fast short-form editing is
inspiration, not a requirement to cram a long explanation into constant cuts.

## 5. Save the research before scripting

Write `topic-research.md` in the episode folder with:

- Retrieval time and Fireship channel URL.
- Observed uploads and inspection depth; access limitations, if any.
- Candidate table: question, source video, primary-source link, dated trend
  evidence, history match, proposed original angle and reason to choose/reject.
- Selected question, why now, intended audience payoff and factual boundaries.
- Editorial techniques borrowed as principles, and the new Richard example.

Carry supporting factual sources into `sources.md` and selected visual ideas
into `STORYBOARD.md`. Research freshness is per production run; never pass a
stale snapshot off as a live check.

## Explicit dashboard topics and revisions

When the owner supplies a topic, preserve it. Fireship and trend research may
help with framing/context, but must not silently replace the requested subject.
A visual/audio revision does not require a new trend search unless the owner
asks for updated factual content or a new topic.
