# Shapiro Law Offices — Redesign Concept

A static-HTML redesign concept for [shapirolawoffices.com](https://www.shapirolawoffices.com/), built to the visual language of [mad4justice.com](https://mad4justice.com/) at the client's request (bold navy/red palette, large display headlines, card-based practice-area layout, case-result strip, credential badges).

**This is a design preview, not the live site.** shapirolawoffices.com is completely unaffected — this repo is hosted separately.

## Content sourcing

All firm facts (attorney bio, address, phone, case results, credentials) are pulled from the real, live shapirolawoffices.com site and the client's Amphs AI profile record — not invented. See notes below on what's real vs. placeholder.

- **Real:** firm name, attorney name/bio facts, address (3205 Grand Concourse, Suite 1, Bronx, NY 10468), phone (718.295.7000), practice-area categories and sub-categories, all five case results with case names and amounts, Super Lawyers / AV Preeminent / published-author credentials.
- **Placeholder (marked in the page itself):** all photography. No attorney headshot, office photo, or book-cover image is licensed for this concept — those sections show a clearly labeled dashed placeholder block ready for real photography to be dropped in.
- **Not wired up:** the contact form is static HTML only; submitting it shows a notice that nothing was sent (no backend attached).

## Structure

```
index.html                              Homepage
about.html                              Attorney profile (Jason Shapiro, Esq.)
practice-areas.html                     Practice areas overview
practice-areas/construction-scaffold.html
practice-areas/motor-vehicle.html
practice-areas/premises.html
practice-areas/medical-malpractice.html
results.html                            Verdicts & settlements
contact.html                            Contact + office map
css/styles.css                          Shared design system
js/main.js                              Mobile nav toggle
```

## Local preview

```
python3 -m http.server 8000
```

Then open `http://localhost:8000/`.

## Deploy

Static site, deployed via GitHub Pages from the `main` branch root.
