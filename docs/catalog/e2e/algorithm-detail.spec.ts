import { test, expect } from '@playwright/test';

test.describe('アルゴリズム詳細ページ (DetailPage)', () => {
  test('アルゴリズムカードをクリックして詳細ページが表示される', async ({ page }) => {
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

    // アルゴリズムタブに切り替え
    await page.getByRole('button', { name: /アルゴリズムから探す/ }).click();

    // アルゴリズムカードをクリック
    const algoCard = page.locator('a[href*="/algorithm/"]').first();
    await expect(algoCard).toBeVisible();
    await algoCard.click();

    // /algorithm/ URLに遷移していること
    await expect(page).toHaveURL(/\/algorithm\//);

    // タイトル（h1またはh2）が表示されること
    const heading = page.locator('h1, h2').first();
    await expect(heading).toBeVisible();
    const headingText = await heading.textContent();
    expect(headingText).toBeTruthy();
    expect(headingText!.trim().length).toBeGreaterThan(0);

    // JSランタイムエラーがないこと
    expect(consoleErrors).toHaveLength(0);
  });

  test('存在するアルゴリズムIDに直接アクセスして描画される', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    page.on('pageerror', (err) => {
      consoleErrors.push(err.message);
    });

    // 既知のアルゴリズムIDに直接アクセス（baseURLに対する相対パス）
    await page.goto('./algorithm/gaussiancopula');

    // ページが空でないこと（白画面チェック）
    const body = page.locator('body');
    await expect(body).not.toBeEmpty();

    // タイトルが表示されること
    const heading = page.locator('h1, h2').first();
    await expect(heading).toBeVisible({ timeout: 10_000 });

    // JSランタイムエラーがないこと
    expect(consoleErrors).toHaveLength(0);
  });
});
