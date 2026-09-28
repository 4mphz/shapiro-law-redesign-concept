# Site-wide design review

Baseline: c01003d. Review branch only. No merge and no edits to the firm's production website.

## Root causes fixed

1. Legacy absolute-positioned bullet pseudo-elements conflicted with newer zero-padding rules. Lists now use native outside markers with consistent indentation. Guide-directory links are explicitly marker-free.
2. Imported copy lacked section containers. Practice pages now use an editorial structure, reading column, on-page navigation, section dividers and native details/summary FAQs.
3. Source consultation text appeared both inline and in the global consultation band. The inline duplicate was removed, while every distinct paragraph remains.
4. Book image sizing inside a shrink-wrapped link computed to zero pixels on the attorneys page. Explicit parent and image widths restore it.
5. Form fields had equal grid spans despite different purposes. The description and matter fields now span the full form. Mobile puts the form before the office details.
6. Default feedback notices and expanded toolbars covered page content. Feedback tools now start collapsed and remain keyboard accessible. An empty status element that intercepted mobile clicks was also fixed.

## Presentation

Shared serif interior headings, restrained navy consultation bands, consistent reading widths and spacing, revised practice cards, guide directory, results hierarchy, attorney profiles, recognition cards, and contact information. The courthouse image and overlays are unchanged. Approved logo, 3D book and portrait remain. Direct directions links replace unreliable embedded maps. Mobile social buttons retain equal sizing.

## Follow-up refinements

- Professional recognition is now a native bullet list on both attorney pages, replacing the four cards.
- Jason's biography uses the existing, uncropped 2026 Top Lawyers event photo (`images/jason-top-lawyers-2026.jpg`) on the English and Spanish attorney pages. The homepage hero portrait is unchanged.
- Opening paragraphs now sit directly beneath their page headline in all 36 interior headers. Their wording is unchanged and the old standalone introductions are removed. Introductory subheadings and existing summaries are preserved within the header.
- Event photo and recognition-list screenshots are included at 390, 768 and 1440 pixels.

The event photo subsequently received a tighter 5:4 in-page crop that focuses on the upper bodies, award and event branding. This uses CSS framing on both attorney pages; the original photograph is unchanged. Checks at five widths are recorded in `event-crop-checks.json`.

Header and footer branding now share a compact HTML/CSS wordmark on all 38 pages, replacing the oversized logo image. Both locations use identical typography, white and site-blue colors, and left-aligned SHAPIRO / LAW OFFICES, PLLC text. The original image asset remains available but is no longer used in either location. Checks at five widths (320, 390, 768, 1024 and 1440 pixels) verify matching markup and dimensions, aligned left edges, no logo images, and no horizontal overflow. All 190 checks passed; results are recorded in `shared-logo-checks.json`, with desktop and mobile header/footer screenshots in `screenshots/shared-logo-*.jpg`.

## Verification

- 38 pages at 320, 390, 768, 1024 and 1440 pixels: 190 page/viewport combinations.
- Checks cover horizontal overflow, broken images, collapsed image dimensions, heading count, broken accessibility labels and detached bullet decorations.
- Visual inspection of home, practice index, construction page, scaffold guide, attorneys, results and contact at desktop and mobile sizes; shared Spanish pages included in regression coverage.
- Interaction tests cover mobile navigation, Escape handling, guide links, FAQ expansion and keyboard collapse, section anchors, long form descriptions and the feedback toolbar.
- All distinct pre-change approved paragraphs, list items and headings remain, except repeated instances of the same consultation text are consolidated. Case results remain at 50.
- The content generator runs the idempotent presentation pass after generating source copy.

The contact form remains a design-preview form without a delivery backend. Tests confirm it says nothing was sent. No real form submissions or feedback comments were sent during testing. External WhatsApp account ownership is not verified by this design pass.

Run `python3 scripts/refine-design.py` after source changes, then `python3 scripts/verify-september.py`, `node scripts/check-design.mjs after` and `node scripts/check-design-interactions.mjs` with the local preview on port 8124.
