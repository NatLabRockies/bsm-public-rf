# bsm-public-rf agent instructions

## Repository purpose

This repository distributes the consumable BSM reduced-form model. Keep it
focused on model loading, inference, schemas, examples, and the model files a
user needs to make predictions.

Publication configurations, execution scripts, diagnostic artifacts, figures,
and scientific workflow tests belong in
`rfm-pipeline/examples/bsm-manuscript/`. Article and submission files belong in
`bsm-public-rf-manuscript`.

## Safety

- Treat `model/` as a versioned public data contract.
- Never reorder coefficient columns or output rows without updating and
  validating every aligned file.
- Do not fabricate model values, hashes, provenance, or publication status.
- The current bundle is an existing interim export; do not attribute it to a
  newer method or run without accepted evidence.
- Do not add manuscript execution or HPC orchestration back to this repository.
- Use Pixi for development commands.
- Add or update tests before changing loader behavior.
- Do not weaken, skip, or narrow tests to make a change pass.

## Git control

This repository is advisory. Work on a task branch. Ask before committing,
pushing, opening a pull request, merging, deleting branches, or rewriting
history unless the user explicitly authorized that exact operation.

## Validation

Run:

```bash
pixi run test
pixi run lint
pixi run format-check
git diff --check
```
