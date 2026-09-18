# Shapiro Law Offices, PLLC redesign concept

This repository contains the review-only website concept for Shapiro Law Offices, PLLC. It is separate from the live firm website at [shapirolawoffices.com](https://www.shapirolawoffices.com/).

## Review links

- GitHub Pages: <https://4mphz.github.io/shapiro-law-redesign-concept/>
- Cloudflare Pages: <https://shapiro-law-redesign-concept.pages.dev/>

The preview includes a feedback overlay for Jason and other reviewers. Add `?review=off` to a page URL only when a clean design screenshot is needed.

## Content and assets

Firm facts, biographies, address, phone number, case results, and credentials come from client-approved materials or the firm&rsquo;s existing public content. The concept uses:

- The supplied Bronx courthouse photograph
- Jason Shapiro&rsquo;s supplied portrait and profile photograph
- The approved three-dimensional book rendering based on the supplied cover
- The supplied Super Lawyers logo
- Licensed supporting practice-area photographs listed in [images/IMAGE-CREDITS.md](images/IMAGE-CREDITS.md)

The current review branch restores the August 24 document's wording verbatim at the user's request. Unfinished attorney and testimonial placeholders are excluded and disclosed in the [copy comparison report](docs/verbatim-copy/index.html). The contact form is a preview interaction and does not send information to the firm.

## Structure

```text
index.html                              English homepage
about.html                              Attorneys
practice-areas.html                     Practice areas overview
practice-areas/*.html                   English practice-area details
results.html                            Verdicts and settlements
contact.html                            Contact and Bronx office
es/index.html                           Spanish homepage
es/about.html                           Spanish attorneys page
es/practice-areas.html                  Spanish practice areas
es/practice-areas/*.html                Spanish practice-area details
es/results.html                         Spanish results
es/contact.html                         Spanish contact page
css/styles.css                          Shared design system
js/main.js                              Navigation and preview feedback UI
worker/                                 Cloudflare feedback service
```

## Local preview

```sh
python3 -m http.server 8000
```

Open <http://localhost:8000/>. Add `?review=off` for clean screenshots.

## Review workflow

Changes are made on a branch and opened as a pull request against `main`. Justin reviews the pull request before anything is merged. GitHub Pages publishes only after a reviewed change reaches `main`.
