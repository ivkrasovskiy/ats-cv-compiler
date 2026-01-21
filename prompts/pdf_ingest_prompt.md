You are given raw text extracted from a PDF CV. Convert it into JSON that matches the provided schema.

Rules:
- Do NOT invent facts (no new employers, titles, dates, metrics, or claims).
- Use only information explicitly present in the text.
- If a field is missing or unclear, output an empty string or empty list.
- Keep bullet wording close to the source text.
- Output JSON only. No extra commentary.

PDF_TEXT:
{{PDF_TEXT}}
