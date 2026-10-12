# Data handling

All real working data is ignored by Git until redistribution terms are confirmed.
Raw downloads stay untouched. Draft extraction goes to `interim/`; human-checked
events go to `clean/`; generated outputs go to `processed/`.

Use the header templates in `templates/`. Lines starting with `#` are instructions,
not records, and are ignored by the project CSV reader. Never mark an agent draft
`verified=Y`. Synthetic data belongs only in `tests/fixtures/`.

