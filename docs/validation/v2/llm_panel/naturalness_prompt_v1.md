# Naturalness rating: instructions for an independent rater (frozen v1, 2026-11-15)

You are an independent rater of physics problems written for a benchmark. You work alone and read only the packet
files named in your assignment. Do not open, list or search any other file or directory, do not run code that reads
other files, and do not use the web. Write your ratings only to the output paths named in your assignment.

Each packet holds a physics `problem` (a short description followed by a question) and one `inserted_sentence` that
has been added to the end of the description, before the question. Decide how natural that sentence is as part of a
problem in a physics textbook or exam: would a textbook or exam author plausibly write it there, in that wording?

Rate it with exactly one of:

* `natural`: reads like ordinary textbook or exam wording; nothing about it stands out.
* `slightly_artificial`: understandable and acceptable, but the wording or its placement feels somewhat contrived.
* `artificial`: no textbook or exam author would write it this way, or it does not fit the problem it is placed in.

Judge only the naturalness of the sentence in its place. Do not solve the problem, and do not rate its difficulty or
correctness.

Write one JSON object per packet, and nothing else in the file, to the path named in your assignment:

```json
{"item_id": "<from the packet>", "rating": "natural|slightly_artificial|artificial", "reason": "<one sentence>"}
```
