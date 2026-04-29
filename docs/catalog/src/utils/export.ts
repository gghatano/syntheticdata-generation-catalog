/**
 * テーブルデータの CSV / Markdown エクスポートユーティリティ
 */

export type TableData = {
  headers: string[];
  rows: string[][];
};

/** CSV 文字列に変換 */
export function toCSV(data: TableData): string {
  const escape = (v: string) => {
    if (v.includes(",") || v.includes('"') || v.includes("\n")) {
      return `"${v.replace(/"/g, '""')}"`;
    }
    return v;
  };
  const lines = [
    data.headers.map(escape).join(","),
    ...data.rows.map((row) => row.map(escape).join(",")),
  ];
  return lines.join("\n");
}

/** Markdown テーブル文字列に変換 */
export function toMarkdown(data: TableData): string {
  const colWidths = data.headers.map((h, i) =>
    Math.max(h.length, ...data.rows.map((r) => (r[i] ?? "").length))
  );

  const pad = (s: string, w: number) => s + " ".repeat(Math.max(0, w - s.length));

  const headerLine =
    "| " + data.headers.map((h, i) => pad(h, colWidths[i])).join(" | ") + " |";
  const separatorLine =
    "| " + colWidths.map((w) => "-".repeat(w)).join(" | ") + " |";
  const bodyLines = data.rows.map(
    (row) =>
      "| " + row.map((cell, i) => pad(cell, colWidths[i])).join(" | ") + " |"
  );

  return [headerLine, separatorLine, ...bodyLines].join("\n");
}

/** CSV ファイルとしてダウンロード */
export function downloadCSV(data: TableData, filename: string): void {
  const bom = "\uFEFF"; // Excel で日本語が文字化けしないよう BOM を付与
  const csv = bom + toCSV(data);
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename.endsWith(".csv") ? filename : `${filename}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/** クリップボードにテキストをコピー */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    // フォールバック: execCommand
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);
    textarea.select();
    const ok = document.execCommand("copy");
    document.body.removeChild(textarea);
    return ok;
  }
}
