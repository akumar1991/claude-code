# Extract PDF Form Fields Command

Extract and display all form fields from a PDF file, including their names, types, current values, and options.

## Instructions

You are tasked with extracting form field information from a PDF file. This is useful for:
- Understanding what data a PDF form requires
- Creating data templates (JSON/CSV) for batch processing
- Debugging form filling issues
- Documenting PDF form structure

### 1. Install Dependencies (if needed)

If the plugin dependencies are not installed, run:
```bash
cd /home/user/claude-code/plugins/pdf-form-filler && npm install
```

### 2. Extract Form Fields

Run the extraction command:
```bash
cd /home/user/claude-code/plugins/pdf-form-filler && npx ts-node lib/pdf-form-filler.ts extract <pdf-file-path>
```

This will output JSON containing all form fields with their properties.

### 3. Interpret the Output

The output will be a JSON array with objects for each field:
```json
[
  {
    "name": "firstName",
    "type": "text",
    "value": ""
  },
  {
    "name": "lastName",
    "type": "text",
    "value": ""
  },
  {
    "name": "agreeToTerms",
    "type": "checkbox",
    "value": false
  },
  {
    "name": "country",
    "type": "dropdown",
    "value": "",
    "options": ["USA", "Canada", "UK", "Other"]
  }
]
```

### 4. Field Types

The following field types are supported:
- **text**: Single-line or multi-line text input
- **checkbox**: Boolean checkbox (true/false)
- **dropdown**: Single-selection dropdown menu
- **radio**: Radio button group (single selection)
- **button**: Push buttons (usually not fillable)
- **unknown**: Unsupported or unrecognized field type

### 5. Present the Information

After extracting fields, present them to the user in a clear format:

#### Option A: Table Format
```
Form Fields in <filename>:

| Field Name        | Type     | Current Value | Options                    |
|-------------------|----------|---------------|----------------------------|
| firstName         | text     | (empty)       |                            |
| lastName          | text     | (empty)       |                            |
| agreeToTerms      | checkbox | false         |                            |
| country           | dropdown | (empty)       | USA, Canada, UK, Other     |
```

#### Option B: Detailed List
```
Found 4 form fields in <filename>:

1. firstName (text)
   - Current value: (empty)

2. lastName (text)
   - Current value: (empty)

3. agreeToTerms (checkbox)
   - Current value: false

4. country (dropdown)
   - Current value: (empty)
   - Options: USA, Canada, UK, Other
```

### 6. Generate Templates (Optional)

If the user wants to fill the form later, offer to create data templates:

#### JSON Template:
```json
{
  "firstName": "",
  "lastName": "",
  "agreeToTerms": false,
  "country": ""
}
```

#### CSV Template:
```csv
firstName,lastName,agreeToTerms,country
```

Save these templates to files if requested.

### 7. Next Steps

After extracting fields, suggest next actions:
- "Would you like me to create a JSON/CSV template for filling this form?"
- "Would you like to fill out this form now? I can ask you for values for each field."
- "Should I save this field information to a file for your reference?"

## Example Workflows

### Example 1: Basic extraction
```
User: What fields are in my application.pdf?
Assistant:
1. Run extraction command
2. Parse JSON output
3. Present fields in a clear table format
4. Ask if they want to create a template or fill the form
```

### Example 2: Extract and create template
```
User: Extract fields from form.pdf and create a JSON template
Assistant:
1. Run extraction command
2. Parse the output
3. Create a JSON template file with empty/default values
4. Save to form-template.json
5. Report success and file location
```

### Example 3: Extract for batch processing
```
User: I need to fill 100 copies of invoice.pdf with different data
Assistant:
1. Extract fields from invoice.pdf
2. Create a CSV template with appropriate headers
3. Explain how to fill the CSV with data
4. Mention the /fill-form command for batch processing
```

## Error Handling

- If the PDF file doesn't exist, report a clear error
- If the PDF has no form fields, inform the user (it may be a static PDF)
- If dependencies are missing, install them first
- If the PDF is encrypted or corrupted, report the specific error

## Output Options

You can save the extracted field information to a file:
```bash
npx ts-node lib/pdf-form-filler.ts extract input.pdf > fields.json
```

## Notes

- This command only reads PDFs, it doesn't modify them
- Some complex PDF forms (especially XFA forms) may not be fully supported
- Signature fields and other advanced field types may appear as "unknown"
- The extraction includes current/default values in the PDF
