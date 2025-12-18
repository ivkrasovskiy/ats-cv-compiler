cv-compiler/ # project root, this folder
  data/                 # your canonical content
  jobs/                 # job descriptions
  templates/            # typst/html/latex templates
  src/
    schema/             # pydantic models
    select/             # scoring + selection logic
    llm/                # providers + prompts
    render/             # pdf/docx generation
    lint/               # checks
  out/
  tests/
  README.md