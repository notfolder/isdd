import { test, expect } from '@playwright/test';
import path from 'path';
// In a real Docker environment, we might need to ensure the test data is accessible.

test.describe('Sigma Plot Web App E2E Flow', () => {
  test('should successfully complete the full analysis flow', async ({ page }) => {
    // 1. Navigate to application
    await page.goto('/');

    // 2. Upload CSV file (using a simulated upload via the browser)
    const filePath = path.join(__dirname, '../../tests/data/sample_numeric.csv');
    // Note: In Playwright, file uploading is typically handled via 'setInputFiles'

    // We need to locate the input element. Streamlit uses a standard file input.
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.getByText(/Upload/i).click(); // Or find the input specifically
    // A more robust way for Streamlit is to use setInputFiles on the input element
    // but let's try locating it first.
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles(filePath);

    // Wait for upload to complete and UI to update with column selection
    await expect(page.getByText(/Select Column A/i)).toBeVisible();

    // 3. Select Columns for analysis (Column A and Column B)
    await page.getByLabel(/Select Column A/i).selectOption({ label: 'column_a' });
    await page.getByLabel(/Select Column B/i).selectOption({ label: 'column_b' });
    // The selectbox might use different labels depending on how Streamlit renders it.
    // We will refine this based on actual behavior if needed, but targeting by label is standard.

    // 4. Run Analysis
    await page.getByRole('button', { name: /Run Analysis/i }).click();

    // 5. Verify Results Page is shown and plots are present
    await expect(page.getByText(/Analysis Results/i)).toBeVisible();
    // Check for presence of visual elements like histogram or Q-Q plot (placeholder check)
    await expect(page.getByText(/Histogram/i)).toBeVisible();
  });

  test('should handle invalid non-numeric column selection', async ({ page }) => {
    // 1. Navigate to application
    await page.goto('/');

    // 2. Upload non-numeric CSV file
    const filePath = path.join(__dirname, '../../tests/data/sample_nonnumeric.csv');
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.getByText(/Upload/i).click(); 
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles(filePath);

    // 3. Select columns (One numeric, one text)
    await expect(page.getByLabel(/Select Column A/i).or(page.locator('select'))).toBeVisible();
    // We'll select the numeric column A and non-numeric B to trigger error logic
    // For this test, we target the names from our sample_nonnumeric.csv file
    await page.getByLabel(/Select Column A/i).selectOption({ label: 'column_a' });
    await page.getByLabel(/Select Column B/i).selectOption({ label: 'text_value' });

    // 4. Attempt to run analysis and check for error message from app logic
    await page.getByRole('button', { name: /Run Analysis/i }).click();
    await expect(page.getByText(/Please select two valid numeric columns/i)).toBeVisible();
  });
});
