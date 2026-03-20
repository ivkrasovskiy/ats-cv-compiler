You are given raw text extracted from a PDF CV. Convert it into JSON that matches the provided schema.

## Core rules
- Do NOT invent facts. No new employers, titles, dates, metrics, or claims.
- Use only information explicitly present in the text.
- If a field is missing or unclear, output an empty string or empty list.
- Output JSON only. No commentary, no markdown fences.

## Projects — always populate this list
The `projects` array must never be empty if the CV has any work history.

**If the CV has an explicit Projects section**: map each project to a projects entry directly.

**If the CV has NO explicit projects section** (most CVs): derive one project entry per role/engagement:
- `name` = the initiative, product, or role title (e.g. "Backend Platform Rebuild", "Senior Engineer at Acme")
- `company` = the employer or client name
- `role` = the job title
- `bullets` = the key outcomes/achievements from that role (verbatim or lightly paraphrased)

**Multiple roles at the same company**: create a separate projects entry for each role.

**Consulting/freelance CVs**: create one entry per client engagement.

## Bullet shape guidance
Prefer: "Achieved X by doing Y, measured by Z" (outcome-first).
Fall back to verbatim source text only when no outcome is stated.

## Experience array
Leave `experience` as an empty list `[]`. All role data goes into `projects`.

## Work mode / location
Work mode (Remote, Hybrid, On-site) and city belong in the `location` field when present.

## Tags
Infer `tags` from technologies, languages, and tools mentioned in each role/project. Leave empty if none are mentioned.

## Skills — always populate this list
Extract skills from any "Skills", "Technical Skills", "Technologies", "Stack", or similar section.
Group them into named categories (e.g. "ML / AI", "Languages", "Tools & Infrastructure").
If the CV lists skills without explicit categories, infer sensible groupings from the skill list.
Each category must have a `name` (string) and `items` (non-empty list of strings).
The `skills` array must never be empty if the CV mentions any tools, languages, or technologies.

## Education
Extract every education entry: universities, degrees, diplomas, bootcamps, certifications, and language proficiency.

**Also look in a "Languages" section** (or similar): for each language with a stated level (e.g. "English — C1", "Spanish — B2", "Russian — Native"), create one education entry:
- `institution` = the language name (e.g. "English", "Spanish", "Russian")
- `degree` = the level or certification (e.g. "C1 / Advanced", "Native", "IELTS 7.5")
- `location` = empty string
- `start_date` / `end_date` = empty strings

For formal education entries provide:
- `institution` — university or school name
- `degree` — the degree (e.g. "BSc Applied Math and Physics", "MSc Computer Science")
- `location` — city/country if stated; otherwise empty string
- `start_date` / `end_date` — use "YYYY-MM" if the month is known, or just "YYYY" if only the year is available; use empty string if unknown

## Dates
Use "YYYY-MM" when the month is known (e.g. "2020-03"), or "YYYY" when only the year is available (e.g. "2020"). Use empty string if the date is completely unknown. For ongoing/current roles use empty string for end_date.

## Email
Put the email address in the top-level `email` field (e.g. `"email": "foo@example.com"`).
Do NOT add it as a link in the `links` array — not even as a `mailto:` URL.

## Links
For profile links such as LinkedIn, GitHub, Telegram, and personal websites:
- Set `label` to the service name (e.g. "LinkedIn", "GitHub", "Telegram")
- Set `url` to the full URL if it appears as visible text (e.g. "linkedin.com/in/foo" → "https://linkedin.com/in/foo")
- If a section at the end of the prompt lists hyperlinks found in PDF annotations, match each URL to the
  correct label by domain: linkedin.com → LinkedIn, github.com → GitHub, t.me → Telegram, etc.
- If no URL can be determined, set `url` to an empty string
- Do NOT include email addresses or `mailto:` links here

PDF_TEXT:
{{PDF_TEXT}}
