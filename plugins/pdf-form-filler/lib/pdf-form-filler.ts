#!/usr/bin/env node

/**
 * PDF Form Filler Library
 *
 * This library provides utilities to fill out PDF forms programmatically.
 * It uses pdf-lib to manipulate PDF files and fill form fields.
 *
 * Installation:
 *   npm install pdf-lib
 *
 * Usage:
 *   import { fillPdfForm, extractFormFields } from './pdf-form-filler';
 */

import { PDFDocument, PDFTextField, PDFCheckBox, PDFDropdown, PDFRadioGroup } from 'pdf-lib';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

export interface FormFieldData {
  name: string;
  value: string | boolean;
}

export interface FormFieldInfo {
  name: string;
  type: 'text' | 'checkbox' | 'dropdown' | 'radio' | 'button' | 'unknown';
  value?: string | boolean;
  options?: string[];
}

/**
 * Extract all form fields from a PDF file
 *
 * @param pdfPath - Path to the input PDF file
 * @returns Array of form field information
 */
export async function extractFormFields(pdfPath: string): Promise<FormFieldInfo[]> {
  try {
    const pdfBuffer = fs.readFileSync(pdfPath);
    const pdfDoc = await PDFDocument.load(pdfBuffer);
    const form = pdfDoc.getForm();
    const fields = form.getFields();

    const fieldInfos: FormFieldInfo[] = [];

    for (const field of fields) {
      const name = field.getName();
      let type: FormFieldInfo['type'] = 'unknown';
      let value: string | boolean | undefined;
      let options: string[] | undefined;

      if (field instanceof PDFTextField) {
        type = 'text';
        value = field.getText() || '';
      } else if (field instanceof PDFCheckBox) {
        type = 'checkbox';
        value = field.isChecked();
      } else if (field instanceof PDFDropdown) {
        type = 'dropdown';
        options = field.getOptions();
        const selected = field.getSelected();
        value = selected.length > 0 ? selected[0] : '';
      } else if (field instanceof PDFRadioGroup) {
        type = 'radio';
        options = field.getOptions();
        value = field.getSelected() || '';
      }

      fieldInfos.push({
        name,
        type,
        value,
        ...(options && { options })
      });
    }

    return fieldInfos;
  } catch (error) {
    throw new Error(`Failed to extract form fields: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * Fill out a PDF form with provided data
 *
 * @param inputPdfPath - Path to the input PDF file with form fields
 * @param outputPdfPath - Path where the filled PDF will be saved
 * @param formData - Object mapping field names to values, or array of FormFieldData
 * @param flatten - Whether to flatten the form (make fields non-editable) after filling
 * @returns Path to the output PDF file
 */
export async function fillPdfForm(
  inputPdfPath: string,
  outputPdfPath: string,
  formData: Record<string, string | boolean> | FormFieldData[],
  flatten: boolean = false
): Promise<string> {
  try {
    // Read the PDF file
    const pdfBuffer = fs.readFileSync(inputPdfPath);
    const pdfDoc = await PDFDocument.load(pdfBuffer);
    const form = pdfDoc.getForm();

    // Convert array format to object format if needed
    const dataMap: Record<string, string | boolean> = Array.isArray(formData)
      ? formData.reduce((acc, field) => ({ ...acc, [field.name]: field.value }), {})
      : formData;

    // Fill form fields
    for (const [fieldName, fieldValue] of Object.entries(dataMap)) {
      try {
        const field = form.getField(fieldName);

        if (field instanceof PDFTextField) {
          field.setText(String(fieldValue));
        } else if (field instanceof PDFCheckBox) {
          if (fieldValue === true || fieldValue === 'true' || fieldValue === 'yes' || fieldValue === '1') {
            field.check();
          } else {
            field.uncheck();
          }
        } else if (field instanceof PDFDropdown) {
          field.select(String(fieldValue));
        } else if (field instanceof PDFRadioGroup) {
          field.select(String(fieldValue));
        }
      } catch (error) {
        console.warn(`Warning: Could not fill field "${fieldName}": ${error instanceof Error ? error.message : String(error)}`);
      }
    }

    // Flatten the form if requested (makes fields non-editable)
    if (flatten) {
      form.flatten();
    }

    // Save the filled PDF
    const pdfBytes = await pdfDoc.save();

    // Ensure output directory exists
    const outputDir = path.dirname(outputPdfPath);
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    fs.writeFileSync(outputPdfPath, pdfBytes);

    return outputPdfPath;
  } catch (error) {
    throw new Error(`Failed to fill PDF form: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * Fill multiple PDF forms with data from an array
 * Useful for batch processing
 *
 * @param templatePdfPath - Path to the template PDF file
 * @param outputDir - Directory where filled PDFs will be saved
 * @param dataArray - Array of data objects, each representing one filled form
 * @param fileNameTemplate - Template for output file names (e.g., "form_{index}.pdf")
 * @param flatten - Whether to flatten forms after filling
 * @returns Array of output file paths
 */
export async function fillMultipleForms(
  templatePdfPath: string,
  outputDir: string,
  dataArray: Array<Record<string, string | boolean>>,
  fileNameTemplate: string = 'form_{index}.pdf',
  flatten: boolean = false
): Promise<string[]> {
  const outputPaths: string[] = [];

  for (let i = 0; i < dataArray.length; i++) {
    const fileName = fileNameTemplate.replace('{index}', String(i + 1));
    const outputPath = path.join(outputDir, fileName);

    await fillPdfForm(templatePdfPath, outputPath, dataArray[i], flatten);
    outputPaths.push(outputPath);
  }

  return outputPaths;
}

/**
 * Load form data from a JSON file
 *
 * @param jsonPath - Path to JSON file containing form data
 * @returns Form data object or array
 */
export function loadFormDataFromJson(jsonPath: string): Record<string, string | boolean> | Array<Record<string, string | boolean>> {
  try {
    const jsonContent = fs.readFileSync(jsonPath, 'utf-8');
    return JSON.parse(jsonContent);
  } catch (error) {
    throw new Error(`Failed to load JSON data: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * Load form data from a CSV file
 * Returns an array of data objects for batch processing
 *
 * @param csvPath - Path to CSV file containing form data
 * @returns Array of form data objects
 */
export function loadFormDataFromCsv(csvPath: string): Array<Record<string, string>> {
  try {
    const csvContent = fs.readFileSync(csvPath, 'utf-8');
    const lines = csvContent.trim().split('\n');

    if (lines.length < 2) {
      throw new Error('CSV file must contain at least a header row and one data row');
    }

    // Parse header
    const headers = lines[0].split(',').map(h => h.trim());

    // Parse data rows
    const dataArray: Array<Record<string, string>> = [];
    for (let i = 1; i < lines.length; i++) {
      const values = lines[i].split(',').map(v => v.trim());
      const dataObj: Record<string, string> = {};

      for (let j = 0; j < headers.length; j++) {
        dataObj[headers[j]] = values[j] || '';
      }

      dataArray.push(dataObj);
    }

    return dataArray;
  } catch (error) {
    throw new Error(`Failed to load CSV data: ${error instanceof Error ? error.message : String(error)}`);
  }
}

// CLI interface when run directly
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const isMainModule = process.argv[1] && (
  process.argv[1] === __filename ||
  process.argv[1].endsWith('pdf-form-filler.ts')
);

if (isMainModule) {
  const args = process.argv.slice(2);

  if (args.length < 1) {
    console.log(`
PDF Form Filler CLI

Usage:
  Extract fields:
    node pdf-form-filler.ts extract <input.pdf>

  Fill form:
    node pdf-form-filler.ts fill <input.pdf> <output.pdf> <data.json> [--flatten]

  Batch fill:
    node pdf-form-filler.ts batch <template.pdf> <output-dir> <data.json|data.csv> [--flatten]

Examples:
  node pdf-form-filler.ts extract form.pdf
  node pdf-form-filler.ts fill form.pdf filled-form.pdf data.json
  node pdf-form-filler.ts fill form.pdf filled-form.pdf data.json --flatten
  node pdf-form-filler.ts batch template.pdf ./output data.csv --flatten
    `);
    process.exit(1);
  }

  const command = args[0];

  (async () => {
    try {
      if (command === 'extract') {
        const pdfPath = args[1];
        if (!pdfPath) {
          throw new Error('PDF path is required');
        }

        const fields = await extractFormFields(pdfPath);
        console.log(JSON.stringify(fields, null, 2));

      } else if (command === 'fill') {
        const [inputPath, outputPath, dataPath, flattenFlag] = args.slice(1);
        if (!inputPath || !outputPath || !dataPath) {
          throw new Error('Input PDF, output PDF, and data file paths are required');
        }

        const flatten = flattenFlag === '--flatten';
        const formData = loadFormDataFromJson(dataPath);

        if (Array.isArray(formData)) {
          throw new Error('For single form filling, data should be an object, not an array. Use "batch" command for arrays.');
        }

        const result = await fillPdfForm(inputPath, outputPath, formData, flatten);
        console.log(`PDF form filled successfully: ${result}`);

      } else if (command === 'batch') {
        const [templatePath, outputDir, dataPath, flattenFlag] = args.slice(1);
        if (!templatePath || !outputDir || !dataPath) {
          throw new Error('Template PDF, output directory, and data file paths are required');
        }

        const flatten = flattenFlag === '--flatten';
        let dataArray: Array<Record<string, string | boolean>>;

        if (dataPath.endsWith('.csv')) {
          dataArray = loadFormDataFromCsv(dataPath);
        } else {
          const data = loadFormDataFromJson(dataPath);
          dataArray = Array.isArray(data) ? data : [data];
        }

        const results = await fillMultipleForms(templatePath, outputDir, dataArray, 'form_{index}.pdf', flatten);
        console.log(`Successfully filled ${results.length} forms:`);
        results.forEach(path => console.log(`  - ${path}`));

      } else {
        throw new Error(`Unknown command: ${command}`);
      }
    } catch (error) {
      console.error('Error:', error instanceof Error ? error.message : String(error));
      process.exit(1);
    }
  })();
}
