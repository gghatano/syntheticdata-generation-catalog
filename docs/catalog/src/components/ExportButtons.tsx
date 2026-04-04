import { useState, useCallback } from "react";
import type { TableData } from "../utils/export";
import { downloadCSV, toMarkdown, copyToClipboard } from "../utils/export";

type ExportButtonsProps = {
  data: TableData;
  filenameBase: string;
};

export function ExportButtons({ data, filenameBase }: ExportButtonsProps) {
  const [copied, setCopied] = useState(false);

  const handleDownloadCSV = useCallback(() => {
    downloadCSV(data, `${filenameBase}_results.csv`);
  }, [data, filenameBase]);

  const handleCopyMarkdown = useCallback(async () => {
    const md = toMarkdown(data);
    const ok = await copyToClipboard(md);
    if (ok) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }, [data]);

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={handleDownloadCSV}
        className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-gray-600 bg-white border border-gray-300 rounded-md hover:bg-gray-50 hover:text-gray-800 transition-colors cursor-pointer"
        title="CSV ファイルとしてダウンロード"
      >
        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
        CSV
      </button>
      <button
        onClick={handleCopyMarkdown}
        className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-gray-600 bg-white border border-gray-300 rounded-md hover:bg-gray-50 hover:text-gray-800 transition-colors cursor-pointer"
        title="Markdown テーブルをクリップボードにコピー"
      >
        {copied ? (
          <>
            <svg className="w-3.5 h-3.5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span className="text-green-600">コピーしました</span>
          </>
        ) : (
          <>
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
            </svg>
            Markdown
          </>
        )}
      </button>
    </div>
  );
}
