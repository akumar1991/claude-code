#!/usr/bin/env node

/**
 * Creates a sample PDF form for testing
 */

import { PDFDocument, PDFTextField, PDFCheckBox, PDFDropdown, StandardFonts } from 'pdf-lib';
import * as fs from 'fs';

async function createSampleForm() {
  // Create a new PDF document
  const pdfDoc = await PDFDocument.create();

  // Add a page
  const page = pdfDoc.addPage([600, 750]);

  // Get fonts
  const font = await pdfDoc.embedFont(StandardFonts.Helvetica);
  const boldFont = await pdfDoc.embedFont(StandardFonts.HelveticaBold);

  // Draw title
  page.drawText('Sample Application Form', {
    x: 50,
    y: 700,
    size: 24,
    font: boldFont,
  });

  // Get the form
  const form = pdfDoc.getForm();

  // Create text fields
  page.drawText('First Name:', { x: 50, y: 650, size: 12, font });
  const firstNameField = form.createTextField('firstName');
  firstNameField.addToPage(page, { x: 150, y: 640, width: 200, height: 20 });

  page.drawText('Last Name:', { x: 50, y: 610, size: 12, font });
  const lastNameField = form.createTextField('lastName');
  lastNameField.addToPage(page, { x: 150, y: 600, width: 200, height: 20 });

  page.drawText('Email:', { x: 50, y: 570, size: 12, font });
  const emailField = form.createTextField('email');
  emailField.addToPage(page, { x: 150, y: 560, width: 250, height: 20 });

  page.drawText('Phone:', { x: 50, y: 530, size: 12, font });
  const phoneField = form.createTextField('phone');
  phoneField.addToPage(page, { x: 150, y: 520, width: 200, height: 20 });

  // Create dropdown
  page.drawText('Country:', { x: 50, y: 490, size: 12, font });
  const countryField = form.createDropdown('country');
  countryField.addOptions(['USA', 'Canada', 'UK', 'Australia', 'Other']);
  countryField.addToPage(page, { x: 150, y: 480, width: 150, height: 20 });

  // Create checkboxes
  page.drawText('Agree to Terms:', { x: 50, y: 450, size: 12, font });
  const agreeField = form.createCheckBox('agreeToTerms');
  agreeField.addToPage(page, { x: 180, y: 445, width: 15, height: 15 });

  page.drawText('Subscribe to Newsletter:', { x: 50, y: 420, size: 12, font });
  const subscribeField = form.createCheckBox('subscribeNewsletter');
  subscribeField.addToPage(page, { x: 230, y: 415, width: 15, height: 15 });

  // Create comments field (multi-line)
  page.drawText('Comments:', { x: 50, y: 380, size: 12, font });
  const commentsField = form.createTextField('comments');
  commentsField.addToPage(page, { x: 50, y: 250, width: 500, height: 120 });
  commentsField.enableMultiline();

  // Add instructions at bottom
  page.drawText('This is a sample form created for testing the PDF Form Filler plugin.', {
    x: 50,
    y: 200,
    size: 10,
    font,
  });
  page.drawText('You can fill this form using the examples/sample-data.json file.', {
    x: 50,
    y: 185,
    size: 10,
    font,
  });

  // Save the PDF
  const pdfBytes = await pdfDoc.save();
  fs.writeFileSync('examples/sample-form.pdf', pdfBytes);

  console.log('✅ Sample form created: examples/sample-form.pdf');
  console.log('\nTo test it, run:');
  console.log('  npx ts-node lib/pdf-form-filler.ts extract examples/sample-form.pdf');
  console.log('  npx ts-node lib/pdf-form-filler.ts fill examples/sample-form.pdf examples/filled-form.pdf examples/sample-data.json');
}

createSampleForm().catch(err => {
  console.error('Error creating sample form:', err);
  process.exit(1);
});
