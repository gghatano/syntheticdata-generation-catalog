import { test, expect } from '@playwright/test';

test.describe('トップページ (ListPage)', () => {
  test('事例カードとアルゴリズムカードが表示される', async ({ page }) => {
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

    // 事例カードが少なくとも1件表示されること
    const caseCards = page.locator('a[href*="/case/"]');
    await expect(caseCards.first()).toBeVisible();
    const caseCount = await caseCards.count();
    expect(caseCount).toBeGreaterThan(0);

    // アルゴリズムタブに切り替えてアルゴリズムカードが表示されること
    await page.getByRole('button', { name: /アルゴリズムから探す/ }).click();
    const algorithmCards = page.locator('a[href*="/algorithm/"]');
    await expect(algorithmCards.first()).toBeVisible();
    const algoCount = await algorithmCards.count();
    expect(algoCount).toBeGreaterThan(0);

    // JSランタイムエラーがないこと
    expect(consoleErrors).toHaveLength(0);
  });
});
