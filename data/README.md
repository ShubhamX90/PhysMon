# Data

Committed data should be sufficient to reproduce benchmark construction decisions without
including large generated artifacts.

- `raw/`: canonical templates and small source-of-truth files.
- `generated/`: rendered problem families; excluded from Git when large.
- `validated/`: post-human-validation family metadata.
- `splits/`: family-level train/dev/test splits.

Splits are always by canonical template family, never by rendered prompt instance, per
proposal §6.3.
