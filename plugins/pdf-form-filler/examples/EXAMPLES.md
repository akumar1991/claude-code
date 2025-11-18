# PDF Form Filler Examples

This directory contains example data files to help you get started with the PDF Form Filler plugin.

## Example Files

### 1. `sample-data.json`
A single record with common form fields. Use this for filling a single PDF form.

**Usage:**
```bash
npx ts-node ../lib/pdf-form-filler.ts fill your-form.pdf filled-form.pdf sample-data.json
```

### 2. `batch-data.json`
Multiple records in JSON format for batch processing.

**Usage:**
```bash
npx ts-node ../lib/pdf-form-filler.ts batch template.pdf ./output batch-data.json
```

### 3. `batch-data.csv`
Multiple records in CSV format for batch processing. CSV is easier to edit in spreadsheet applications.

**Usage:**
```bash
npx ts-node ../lib/pdf-form-filler.ts batch template.pdf ./output batch-data.csv
```

## Quick Start Workflow

### Step 1: Extract Fields from Your PDF
First, see what fields your PDF contains:

```bash
cd /home/user/claude-code/plugins/pdf-form-filler
npx ts-node lib/pdf-form-filler.ts extract your-form.pdf
```

This will output JSON like:
```json
[
  {
    "name": "firstName",
    "type": "text",
    "value": ""
  },
  {
    "name": "agreeToTerms",
    "type": "checkbox",
    "value": false
  }
]
```

### Step 2: Create Your Data File
Create a JSON file matching the field names from step 1:

```json
{
  "firstName": "Your Name",
  "agreeToTerms": true
}
```

### Step 3: Fill the Form
```bash
npx ts-node lib/pdf-form-filler.ts fill your-form.pdf filled-form.pdf your-data.json --flatten
```

## Common Scenarios

### Scenario 1: Job Application
You have a job application PDF and want to fill it with your information.

1. Extract fields: `npx ts-node lib/pdf-form-filler.ts extract application.pdf > fields.json`
2. Create your data based on `fields.json`
3. Fill: `npx ts-node lib/pdf-form-filler.ts fill application.pdf my-application.pdf my-info.json --flatten`

### Scenario 2: Batch Invoices
You need to create 50 invoices for different customers.

1. Extract fields from invoice template
2. Create `customers.csv` with columns matching field names
3. Batch fill: `npx ts-node lib/pdf-form-filler.ts batch invoice-template.pdf ./invoices customers.csv --flatten`

### Scenario 3: Event Registration
Fill multiple registration forms with attendee data.

1. Extract fields from registration form
2. Create `attendees.csv` with attendee information
3. Batch fill: `npx ts-node lib/pdf-form-filler.ts batch registration.pdf ./registrations attendees.csv`

## Field Type Examples

### Text Fields
```json
{
  "firstName": "John",
  "lastName": "Doe",
  "address": "123 Main St"
}
```

### Checkboxes
```json
{
  "agreeToTerms": true,
  "subscribeNewsletter": false
}
```

Or use string values:
```json
{
  "agreeToTerms": "true",
  "subscribeNewsletter": "false"
}
```

### Dropdowns
Must match exact option value:
```json
{
  "country": "USA",
  "state": "California"
}
```

### Radio Buttons
Select one option:
```json
{
  "gender": "Male",
  "contactPreference": "Email"
}
```

## Tips

1. **Always extract first**: Use `/extract-fields` or the extract command to understand your PDF structure before filling.

2. **Test without flattening**: Remove `--flatten` flag while testing so you can edit the PDF if something goes wrong.

3. **Use CSV for batch**: For batch processing, CSV files are easier to create and edit in Excel or Google Sheets.

4. **Match field names exactly**: Field names are case-sensitive. Use the exact names from the extract output.

5. **Verify dropdown options**: For dropdown fields, the value must match one of the available options exactly.

## Troubleshooting

### Issue: Fields appear empty after filling
**Solution**: Open the PDF in different PDF readers. Some readers don't display certain field types correctly.

### Issue: "Could not fill field" warning
**Solution**: Check that:
- Field name matches exactly (case-sensitive)
- Value type is correct (e.g., boolean for checkbox)
- For dropdowns, value matches an available option

### Issue: PDF has no form fields
**Solution**: The PDF might be a static document without form fields. You cannot fill static PDFs programmatically.

## Advanced: Creating Template from Extract

Save extraction output as a template:
```bash
npx ts-node lib/pdf-form-filler.ts extract form.pdf > template.json
```

Edit `template.json` to add your values, then use it to fill:
```bash
npx ts-node lib/pdf-form-filler.ts fill form.pdf filled.pdf template.json
```
