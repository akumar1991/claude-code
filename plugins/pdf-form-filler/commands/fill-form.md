# PDF Form Filler Command

Fill out a PDF form with provided data from JSON, CSV, or interactive input.

## Instructions

You are tasked with filling out a PDF form. Follow these steps:

### 1. Understand the Request

The user will provide:
- **Input PDF path**: The PDF file containing form fields to fill
- **Output PDF path**: Where to save the filled PDF (optional, defaults to `{input}-filled.pdf`)
- **Data source**: One of the following:
  - JSON file path containing field data
  - CSV file path for batch processing
  - Interactive mode (ask user for each field)
  - Inline data as key-value pairs

### 2. Install Dependencies (if needed)

If the plugin dependencies are not installed, run:
```bash
cd /home/user/claude-code/plugins/pdf-form-filler && npm install
```

### 3. Extract Form Fields (if needed)

If the user hasn't provided data, first extract the form fields to understand what needs to be filled:

```bash
cd /home/user/claude-code/plugins/pdf-form-filler && npx ts-node lib/pdf-form-filler.ts extract <input-pdf-path>
```

This will show all available form fields with their types and current values.

### 4. Prepare Data

Depending on the data source:

#### Option A: JSON File
Create or use a JSON file with field mappings:
```json
{
  "fieldName1": "value1",
  "fieldName2": "value2",
  "checkboxField": true
}
```

#### Option B: CSV File (for batch processing)
Create or use a CSV file with headers matching field names:
```csv
fieldName1,fieldName2,checkboxField
value1,value2,true
value3,value4,false
```

#### Option C: Interactive Mode
Ask the user for values for each field based on the extracted field information.

### 5. Fill the Form

#### Single Form:
```bash
cd /home/user/claude-code/plugins/pdf-form-filler && npx ts-node lib/pdf-form-filler.ts fill <input-pdf> <output-pdf> <data.json> [--flatten]
```

#### Batch Processing (CSV or JSON array):
```bash
cd /home/user/claude-code/plugins/pdf-form-filler && npx ts-node lib/pdf-form-filler.ts batch <template-pdf> <output-directory> <data.csv|data.json> [--flatten]
```

### 6. Options

- `--flatten`: Make form fields non-editable after filling (recommended for final documents)

### 7. Verify and Report

After filling the form:
- Confirm the output file was created successfully
- Report the location of the filled PDF(s)
- If batch processing, report the number of forms created

## Example Workflows

### Example 1: Fill a single form interactively
```
User: Fill out my job-application.pdf
Assistant:
1. Extract fields from job-application.pdf
2. Ask user for values for each field
3. Create a temporary JSON file with the data
4. Fill the form and save as job-application-filled.pdf
5. Report success
```

### Example 2: Fill form from existing JSON
```
User: Fill out form.pdf using data.json
Assistant:
1. Validate that both files exist
2. Run: npx ts-node lib/pdf-form-filler.ts fill form.pdf form-filled.pdf data.json --flatten
3. Report success and output location
```

### Example 3: Batch process from CSV
```
User: Fill out invoice-template.pdf for all entries in customers.csv
Assistant:
1. Run: npx ts-node lib/pdf-form-filler.ts batch invoice-template.pdf ./invoices customers.csv --flatten
2. Report number of invoices created and output directory
```

## Error Handling

- If dependencies are missing, install them first
- If a field name in the data doesn't exist in the PDF, log a warning but continue
- If the PDF doesn't have any form fields, report an error
- If file paths are invalid, report clear error messages

## Best Practices

- Always use `--flatten` for final documents to prevent further editing
- For batch processing, create a dedicated output directory
- Validate data before filling to catch errors early
- Show a preview of fields and their values before filling if the user seems uncertain

## Notes

- This command uses the `pdf-lib` library for PDF manipulation
- The TypeScript code is located in `plugins/pdf-form-filler/lib/pdf-form-filler.ts`
- Both AcroForm fields and XFA forms are supported (where possible)
- Field types supported: text, checkbox, dropdown, radio buttons
