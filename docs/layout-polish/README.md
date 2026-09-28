# Layout polish and 3D book

Baseline: f7616a3. This pass preserves the website copy, supplied logo, courthouse background, and existing overlay settings.

Changes:
- Mobile hero headline spans the available width instead of crowding the portrait.
- Portrait, author credentials, and book occupy distinct areas. Portrait fades into the background at its lower edge.
- Actual cover is presented as a generated 3D hardcover with spine and page edges, in the hero and book sections in English and Spanish.
- Body paragraphs have consistent reading size, line spacing, and margins.
- Reduced excess spacing between introductory and results sections.
- Removed fixed minimum height on homepage result cards.
- Improved contact guidance list spacing and practice-area link spacing.
- Preserved source copy, all 50 results, existing header controls, and approved statistics.

Before and after images: `screenshots/`. Responsive test output: `after-checks.json`.
Tested representative home, attorneys, contact, results, practice overview, scaffold guide, and Spanish home at 320, 390, 768, 1024, and 1440 pixels.

## Generated asset

Mode: built-in image generation, transparent background.
Input: `images/lawyers-guide-actual-cover.png`.
Output: `images/lawyers-guide-book-3d.png`.
The original source image remains unchanged. This is an illustrative product mockup, not a photograph of the physical binding.

Prompt:

Use case: product-mockup / precise-object-edit. Edit target: supplied actual book cover. Create a photorealistic 3D hardcover book product cutout for a sophisticated law firm website. Preserve the front cover artwork exactly, including Jason's photograph, courthouse, title THE LAWYERS’ GUIDE TO PERSONAL INJURY LAW, author JASON SHAPIRO, ESQ., and existing badge. Do not redesign or invent a different cover or face. Upright closed hardcover book, slight three-quarter perspective, front cover largely readable, visible narrow spine on left and cream page edges at top/right, believable 1.25-inch thickness, crisp binding and subtle studio highlights. Single book only, complete uncropped silhouette, close framing with small transparent margins. Genuine transparent background, no backdrop, no floor rectangle, no props, no extra text. Restrained natural product shadow.
