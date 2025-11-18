# PDF Form Filler Plugin

A Claude Code plugin for programmatically filling out PDF forms with data from JSON, CSV, or interactive input.

## Features

- ✅ Extract form fields from PDF files
- ✅ Fill PDF forms with data from JSON or CSV files
- ✅ Interactive form filling with guided prompts
- ✅ Batch processing for multiple forms
- ✅ Support for text fields, checkboxes, dropdowns, and radio buttons
- ✅ Option to flatten forms (make fields non-editable)
- ✅ Generate data templates from existing PDFs

## Installation

1. Navigate to the plugin directory:
```bash
cd plugins/pdf-form-filler
```

2. Install dependencies:
```bash
npm install
```

## Usage

### Slash Commands

This plugin provides two slash commands for use in Claude Code:

#### `/fill-form` - Fill out a PDF form

Fill a PDF form with provided data from various sources.

**Examples:**
```
/fill-form application.pdf with data.json
/fill-form invoice-template.pdf using customers.csv (batch mode)
/fill-form contract.pdf (interactive mode)
```

#### `/extract-fields` - Extract form fields from a PDF

Analyze a PDF and list all form fields with their types and options.

**Examples:**
```
/extract-fields application.pdf
/extract-fields form.pdf and create a JSON template
```

### Direct CLI Usage

You can also use the TypeScript library directly without Claude Code:

#### Extract Form Fields
```bash
npx ts-node lib/pdf-form-filler.ts extract input.pdf
```

**Output:**
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

#### Fill a Single Form
```bash
npx ts-node lib/pdf-form-filler.ts fill input.pdf output.pdf data.json
```

**With flattening (recommended for final documents):**
```bash
npx ts-node lib/pdf-form-filler.ts fill input.pdf output.pdf data.json --flatten
```

#### Batch Fill Multiple Forms
```bash
npx ts-node lib/pdf-form-filler.ts batch template.pdf ./output-dir data.csv --flatten
```

## Data Formats

### JSON Format

**Single form:**
```json
{
  "firstName": "John",
  "lastName": "Doe",
  "email": "john.doe@example.com",
  "agreeToTerms": true,
  "country": "USA"
}
```

**Multiple forms (batch):**
```json
[
  {
    "firstName": "John",
    "lastName": "Doe",
    "email": "john.doe@example.com"
  },
  {
    "firstName": "Jane",
    "lastName": "Smith",
    "email": "jane.smith@example.com"
  }
]
```

### CSV Format

For batch processing, create a CSV file with headers matching field names:

```csv
firstName,lastName,email,agreeToTerms,country
John,Doe,john.doe@example.com,true,USA
Jane,Smith,jane.smith@example.com,false,Canada
Bob,Johnson,bob.j@example.com,true,UK
```

## Supported Field Types

| Field Type | Support | Notes |
|------------|---------|-------|
| Text Fields | ✅ Full | Single-line and multi-line |
| Checkboxes | ✅ Full | Boolean values or "true"/"false" strings |
| Dropdown Menus | ✅ Full | Must match exact option values |
| Radio Buttons | ✅ Full | Single selection from options |
| Signature Fields | ⚠️ Limited | May appear as unknown type |
| XFA Forms | ⚠️ Limited | Basic support only |

## Programmatic Usage

You can also use the library in your own TypeScript/JavaScript code:

```typescript
import { fillPdfForm, extractFormFields } from './lib/pdf-form-filler';

// Extract fields
const fields = await extractFormFields('input.pdf');
console.log(fields);

// Fill form
await fillPdfForm(
  'input.pdf',
  'output.pdf',
  {
    firstName: 'John',
    lastName: 'Doe',
    agreeToTerms: true
  },
  true // flatten
);

// Batch fill
import { fillMultipleForms } from './lib/pdf-form-filler';

await fillMultipleForms(
  'template.pdf',
  './output',
  [
    { name: 'John', email: 'john@example.com' },
    { name: 'Jane', email: 'jane@example.com' }
  ],
  'invoice_{index}.pdf',
  true // flatten
);
```

## Common Use Cases

### 1. Job Applications
Fill out multiple job applications with your standard information:
```
/extract-fields application.pdf and create template
(Edit the template with your information)
/fill-form application.pdf with my-info.json --flatten
```

### 2. Batch Invoices
Generate invoices for multiple customers:
```
/extract-fields invoice-template.pdf
(Create customers.csv with invoice data)
/fill-form invoice-template.pdf using customers.csv
```

### 3. Contracts
Fill out a contract with specific terms:
```
/fill-form contract.pdf
(Claude will interactively ask for each field)
```

### 4. Tax Forms
Prepare tax forms with calculated values:
```
(Prepare tax-data.json with all values)
/fill-form tax-form.pdf with tax-data.json --flatten
```

## Tips

1. **Always flatten final documents**: Use `--flatten` to make forms non-editable when you're done filling them.

2. **Extract fields first**: Before filling a form, use `/extract-fields` to see what data you need.

3. **Test without flattening**: When testing, don't use `--flatten` so you can open the PDF and verify the values.

4. **Use batch mode for efficiency**: If you need to fill the same form multiple times, use batch mode with CSV data.

5. **Keep templates**: Save extracted field templates as starter files for future use.

## Troubleshooting

### "Failed to extract form fields"
- The PDF might not contain fillable form fields
- The PDF might be encrypted or password-protected
- Try opening the PDF in a PDF reader to verify it has form fields

### "Could not fill field"
- Field name might be misspelled in your data
- Field type mismatch (e.g., text value for checkbox)
- Field might be read-only or calculated

### "npm install fails"
- Ensure you have Node.js 18+ installed
- Try deleting `node_modules` and `package-lock.json` and running `npm install` again

### Forms appear blank after filling
- The PDF might be using a non-standard form format
- Try without `--flatten` flag to see if fields are filled
- Some PDF viewers may not display certain field types correctly

## Dependencies

- [pdf-lib](https://github.com/Hopding/pdf-lib) - PDF manipulation library
- Node.js 18 or higher
- TypeScript 5.0+

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Related Resources

- [pdf-lib documentation](https://pdf-lib.js.org/)
- [Claude Code documentation](https://docs.claude.com/en/docs/claude-code)
- [PDF form fields specification](https://opensource.adobe.com/dc-acrobat-sdk-docs/pdfstandards/PDF32000_2008.pdf)

## Support

For issues or questions:
- Create an issue on GitHub
- Check the Claude Code documentation
- Review the examples in this README
