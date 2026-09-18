# August 24 document copy restoration

The user requested the August 24 document's exact wording across the website, superseding the prior selective copy reconciliation. All 18 English and Spanish pages now use the document's supplied text, capitalization, punctuation, metadata, image descriptions and form labels.

This restores the document's original homepage headings, complete attorney and book descriptions, practice lists, Why Choose Us content, homepage contact form, shared consultation copy and result amounts. It removes later marketing copy and recovery totals that are absent from this source.

The existing courthouse, portrait, book artwork, logo, navigation and feedback tools remain. Layout accommodates the longer source passages.

## Evidence

Open `index.html` in this folder for all 18 pages' desktop and mobile comparisons, actual text differences, source paragraphs and exact matching results. Screenshots compare the prior branch preview at commit `d4615c5` against this revision, at identical viewport sizes.

- `source-manifest.json`: source paragraph IDs, roles, exact wording and source DOCX checksum.
- `verification.json`: 677 exact record checks across 18 pages, including repeated shared copy.
- `browser-checks.json`: desktop and mobile checks for overflow and broken images.
- `before-after-text.json`: actual page text before and after.
- `screenshots/`: before and after captures for each page and device.

## Editorial exclusions

26 placeholder entries are excluded: the unfinished second-attorney profiles and pending review sections in both languages. The comparison report lists every excluded entry verbatim. Document usage instructions, structural labels and the final list asking Jason for assets are editorial material, not published website text.

The restored forms use the existing preview interaction and do not submit inquiries to the firm. PR #10 remains the review location. This change does not merge to main or change the firm's official website.
