You are given raw text extracted from a PDF CV. Convert it into JSON that matches the provided schema.

Rules:
- Do NOT invent facts (no new employers, titles, dates, metrics, or claims).
- Use only information explicitly present in the text.
- If a field is missing or unclear, output an empty string or empty list.
- Keep bullet wording close to the source text.
- Output JSON only. No extra commentary.
- Place each role/experience entry into the projects list; leave experience as an empty list.
- In projects, `name` is the project/role label (NOT the employer name).
- In projects, `company` is the employer/organization name.
- Work mode/location (e.g., Remote/Hybrid/City) belongs in `location` when present.

PDF_TEXT:
{{PDF_TEXT}}
