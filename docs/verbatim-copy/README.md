# Approved design with August 24 document copy

All 18 English and Spanish pages use the approved components from commit `d4615c5`, with the August 24 document's passages placed inside those components. The original typography, photographs, cards, section treatments, contact layout and complete footer are preserved.

The user explicitly confirmed that Jason's newer approved figures take precedence over the document's older results. The $300M+ results total, 50+ recoveries and newer case amounts remain. The confirmed Ernest Buonocore profile and approved design labels also remain. There are 649 exact document record matches and 28 explicit older-result overrides.

The document's longer descriptions, practice lists, Why Choose Us copy and homepage contact form are accommodated using the existing design system, with a small supplemental stylesheet for spacing and wrapping.

## Evidence

Open `index.html` in this folder for all 18 pages' desktop and mobile comparisons, actual text differences, source paragraphs and exact matching results. Screenshots compare the stripped-down revision at commit `3ba90d9` against the restored design at identical viewport sizes. Separate screenshots retain the approved `d4615c5` design reference.

- `source-manifest.json`: source paragraph IDs, roles, exact wording and source DOCX checksum.
- `verification.json`: 649 exact record checks across 18 pages, plus explicit approved-result overrides.
- `browser-checks.json`: desktop and mobile checks for overflow and broken images.
- `before-after-text.json`: actual page text before and after.
- `screenshots/`: before and after captures for each page and device.

## Editorial exclusions

26 placeholder entries are excluded: the unfinished second-attorney profiles and pending review sections in both languages. The comparison report lists every excluded entry verbatim. Document usage instructions, structural labels and the final list asking Jason for assets are editorial material, not published website text.

The restored forms use the existing preview interaction and do not submit inquiries to the firm. PR #10 remains the review location. Regenerate the page mapping with `scripts/apply_copy_to_approved_design.py`, then verify with `scripts/verify_document_copy.py`. This change does not merge to main or change the firm's official website.
