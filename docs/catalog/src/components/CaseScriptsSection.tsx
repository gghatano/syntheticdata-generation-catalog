import { buildBlobUrl, buildRawUrl } from "../constants/repo";
import { SCRIPT_ROLE_LABELS } from "../types/experiment-case";
import type { CaseScript, ScriptRole } from "../types/experiment-case";

const ROLE_ORDER: ScriptRole[] = ["prepare", "synthesize", "evaluate"];

function ExternalLinkIcon() {
  return (
    <svg
      className="w-3.5 h-3.5 inline-block"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
      />
    </svg>
  );
}

function DownloadIcon() {
  return (
    <svg
      className="w-3.5 h-3.5 inline-block"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M7 10l5 5m0 0l5-5m-5 5V4"
      />
    </svg>
  );
}

function ScriptRow({ script }: { script: CaseScript }) {
  const fileName = script.path.split("/").pop() ?? script.path;
  return (
    <li className="flex flex-wrap items-baseline gap-x-3 gap-y-1 py-1.5">
      <code className="text-xs font-mono text-gray-700 break-all">{script.path}</code>
      {script.description ? (
        <span className="text-xs text-gray-500">— {script.description}</span>
      ) : null}
      <span className="ml-auto inline-flex items-center gap-2">
        <a
          href={buildBlobUrl(script.path)}
          target="_blank"
          rel="noopener noreferrer"
          aria-label={`${fileName} を GitHub で表示`}
          className="inline-flex items-center gap-1 text-xs text-blue-700 hover:text-blue-900 hover:underline"
        >
          <ExternalLinkIcon />
          コード
        </a>
        <a
          href={buildRawUrl(script.path)}
          target="_blank"
          rel="noopener noreferrer"
          download={fileName}
          aria-label={`${fileName} をダウンロード`}
          className="inline-flex items-center gap-1 text-xs text-blue-700 hover:text-blue-900 hover:underline"
        >
          <DownloadIcon />
          DL
        </a>
      </span>
    </li>
  );
}

export function CaseScriptsSection({ scripts }: { scripts?: CaseScript[] }) {
  if (!scripts || scripts.length === 0) return null;

  const grouped = ROLE_ORDER.map((role) => ({
    role,
    items: scripts.filter((s) => s.role === role),
  })).filter((g) => g.items.length > 0);

  if (grouped.length === 0) return null;

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6 mb-6">
      <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
        使用したスクリプト
      </h2>
      <div className="space-y-4">
        {grouped.map(({ role, items }) => (
          <div key={role}>
            <h3 className="text-xs font-semibold text-gray-600 mb-1">
              {SCRIPT_ROLE_LABELS[role]}
              <span className="ml-2 text-[10px] font-normal text-gray-400">{items.length}件</span>
            </h3>
            <ul className="divide-y divide-gray-100">
              {items.map((script) => (
                <ScriptRow key={`${script.role}-${script.path}`} script={script} />
              ))}
            </ul>
          </div>
        ))}
      </div>
      <p className="text-xs text-gray-400 mt-4 leading-relaxed">
        実行には共通ヘルパー（<code className="text-[11px]">libs/common/experiment.py</code>）と各ライブラリの uv 環境が必要です。詳細はリポジトリの README とプロジェクト直下の <code className="text-[11px]">CLAUDE.md</code> を参照してください。
      </p>
    </div>
  );
}
