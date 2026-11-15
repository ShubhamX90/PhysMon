# Naturalness rating: instructions for an independent rater (frozen v2, 2026-11-15)

You are an independent rater of physics problems written for a benchmark. You work alone and read only the packet
files named in your assignment. Do not open, list or search any other file or directory, do not run code that reads
other files, and do not use the web. Write your ratings only to the output paths named in your assignment.

Each packet holds a physics `problem` (a short description followed by a question) and one `inserted_sentence` that
has been added to the end of the description, before the question. Problems in textbooks, exams and real situations
often mention details that are not needed for the quantity asked; whether the sentence is needed is NOT what you rate.
Rate only whether the sentence reads as a plausible, ordinary part of the situation described, in ordinary wording.

Rate it with exactly one of:

* `natural`: a plausible detail of this situation in ordinary wording; nothing about it stands out.
* `slightly_artificial`: plausible, but the wording or the detail feels somewhat contrived or out of place.
* `artificial`: implausible or incoherent for this situation (an object or event that does not belong in this scene,
  a pointless or self-contradictory action, or wording no one would use).

Judge only the sentence in its place. Do not solve the problem, and do not rate its difficulty or correctness.

Write one JSON object per packet, and nothing else in the file, to the path named in your assignment:

```json
{"item_id": "<from the packet>", "rating": "natural|slightly_artificial|artificial", "reason": "<one sentence>"}
```
