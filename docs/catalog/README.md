# 合成データ生成カタログ (syntheticdata-generation-catalog)

React + TypeScript + Vite で構築されたカタログサイトです。

## テスト実行方法

### Unit テスト

```bash
npm test -- --run
```

### E2E テスト（Playwright）

初回のみ Playwright ブラウザをインストールしてください:

```bash
npx playwright install --with-deps chromium
```

E2E テストの実行:

```bash
npm run test:e2e
```

UI モードで実行（インタラクティブなデバッグ用）:

```bash
npm run test:e2e:ui
```

---

# React + TypeScript + Vite (Original Template)

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react/README.md) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type aware lint rules:

- Configure the top-level `parserOptions` property like this:

```js
export default tseslint.config({
  languageOptions: {
    // other options...
    parserOptions: {
      project: ['./tsconfig.node.json', './tsconfig.app.json'],
      tsconfigRootDir: import.meta.dirname,
    },
  },
})
```

- Replace `tseslint.configs.recommended` to `tseslint.configs.recommendedTypeChecked` or `tseslint.configs.strictTypeChecked`
- Optionally add `...tseslint.configs.stylisticTypeChecked`
- Install [eslint-plugin-react](https://github.com/jsx-eslint/eslint-plugin-react) and update the config:

```js
// eslint.config.js
import react from 'eslint-plugin-react'

export default tseslint.config({
  // Set the react version
  settings: { react: { version: '18.3' } },
  plugins: {
    // Add the react plugin
    react,
  },
  rules: {
    // other rules...
    // Enable its recommended rules
    ...react.configs.recommended.rules,
    ...react.configs['jsx-runtime'].rules,
  },
})
```

## SPA ルーティングと GitHub Pages の制約

### 現在の挙動

このカタログサイトは React Router の `BrowserRouter` を使用している。
GitHub Pages へのデプロイ時、`index.html` を `404.html` にコピーすることで SPA のルーティングを実現している（`.github/workflows/deploy-pages.yml` 参照）。

### 既知の制約

`/case/:id` や `/algorithm/:id` などのルートに直接アクセス（またはリロード）すると、
GitHub Pages は **HTTP 404 ステータス**で応答する。

ブラウザで開いた場合は `404.html`（= `index.html` のコピー）がフォールバックとして返され、
React Router が URL を解釈してルーティングを復元するため**画面上は正常に表示される**。
しかしステータスコードは 404 のままであるため、以下の影響がある：

- 検索エンジン・SNS クローラー・OGP 取得系ツールが「存在しないページ」として扱う
- 監視ツール（UptimeRobot 等）で誤検知される可能性がある

### 監視ツールを使用する場合の推奨

監視系ツールを接続する際は、`/case/:id` 等の個別ルートではなくトップの `/` のみを監視対象にすることを推奨する。

### 将来対応の選択肢

| 案 | 内容 | 備考 |
|---|---|---|
| 案1 | `HashRouter` に切り替え（URL が `/#/case/:id` 形式になる） | SEO・ステータス問題が解消。URL の見栄えは変わる |
| 案2 | Cloudflare Pages / Netlify に移行 | リダイレクトルールで SPA を適切に扱える。インフラ変更大 |

OGP 対応や SEO を重視する段階になったら案1への切替を検討する。
