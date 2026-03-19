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

PDF_TEXT:
{{PDF_TEXT}}
