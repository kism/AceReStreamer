# Documentation Extensions

## generate_json_examples.py

This Sphinx extension automatically generates valid JSON examples from Pydantic models during the documentation build process.

### Purpose

This ensures that JSON examples in the documentation are always valid and in sync with the actual Pydantic model definitions in the code.

### How it works

1. During the Sphinx build process (`builder-inited` event), the extension imports the Pydantic models
2. It creates example instances with representative data
3. It serializes them to JSON using `model_dump(mode="json")`
4. It writes the JSON files to `docs/generated/`

### Generated files

- `iptv_example.json` - Example of ScrapeSiteIPTV model
- `html_example.json` - Example of ScrapeSiteHTML model
- `api_example.json` - Example of ScrapeSiteAPI model

### Usage in markdown

The generated JSON files are included in the markdown documentation using MyST's literalinclude directive:

\`\`\`markdown
\`\`\`{literalinclude} generated/iptv_example.json
:language: json
\`\`\`
\`\`\`

### Updating examples

To modify the examples, edit the `generate_json_examples()` function in this extension. The examples will be regenerated on each documentation build.
