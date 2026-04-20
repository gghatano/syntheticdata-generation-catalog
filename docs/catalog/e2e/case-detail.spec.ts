import { test, expect } from '@playwright/test';

test.describe('事例詳細ページ (CaseDetailPage)', () => {
  test('事例一覧から詳細ページに遷移してタイトルと結果テーブルが表示される', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    page.on('pageerror', (err) => {
      consoleErrors.push(err.message);
    });

    await page.goto('./');

    // 事例カードをクリック
    const caseCard = page.locator('a[href*="/case/"]').first();
    await expect(caseCard).toBeVisible();
    await caseCard.click();

    // /case/ URLに遷移していること
    await expect(page).toHaveURL(/\/case\//);

    // タイトル（h1またはh2）が表示されること
    const heading = page.locator('h1, h2').first();
    await expect(heading).toBeVisible();
    const headingText = await heading.textContent();
    expect(headingText).toBeTruthy();
    expect(headingText!.trim().length).toBeGreaterThan(0);

    // 結果テーブルが表示されること（tableタグ）
    const resultTable = page.locator('table');
    await expect(resultTable.first()).toBeVisible();

    // テーブルに行データが存在すること
    const tableRows = page.locator('table tbody tr');
    const rowCount = await tableRows.count();
    expect(rowCount).toBeGreaterThan(0);

    // JSランタイムエラーがないこと
    expect(consoleErrors).toHaveLength(0);
  });

  test('存在する事例IDに直接アクセスして描画される', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    page.on('pageerror', (err) => {
      consoleErrors.push(err.message);
    });

    // 既知の事例IDに直接アクセス（baseURLに対する相対パス）
    await page.goto('./case/adult-census-anonymization');

    // ページが空でないこと（白画面チェック）
    const body = page.locator('body');
    await expect(body).not.toBeEmpty();

    // タイトルが表示されること
    const heading = page.locator('h1, h2').first();
    await expect(heading).toBeVisible({ timeout: 10_000 });

    // 結果テーブルが表示されること
    const resultTable = page.locator('table');
    await expect(resultTable.first()).toBeVisible();

    // JSランタイムエラーがないこと
    expect(consoleErrors).toHaveLength(0);
  });
});
