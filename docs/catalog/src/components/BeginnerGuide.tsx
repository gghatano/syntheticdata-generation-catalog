import { useState, useEffect } from "react";
import { Link } from "react-router-dom";

const STORAGE_KEY = "beginner-guide-closed";

export function BeginnerGuide() {
  const [isOpen, setIsOpen] = useState(() => {
    return localStorage.getItem(STORAGE_KEY) !== "true";
  });

  useEffect(() => {
    if (!isOpen) {
      localStorage.setItem(STORAGE_KEY, "true");
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, [isOpen]);

  return (
    <div className="mb-6">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between bg-blue-50 border border-blue-200 rounded-t-lg px-5 py-3 text-left hover:bg-blue-100 transition-colors"
        style={{
          borderRadius: isOpen ? "0.5rem 0.5rem 0 0" : "0.5rem",
        }}
      >
        <span className="font-semibold text-blue-800 flex items-center gap-2">
          <span>&#x1F530;</span> 初めての方へ：どの手法を選べばいいか迷ったら
        </span>
        <span className="text-blue-400 text-sm shrink-0 ml-2">
          {isOpen ? "▲ 閉じる" : "▼ 開く"}
        </span>
      </button>

      {isOpen && (
        <div className="bg-blue-50 border border-t-0 border-blue-200 rounded-b-lg px-5 py-4 border-l-4 border-l-blue-400">
          <p className="text-sm text-blue-900 mb-4">
            あなたのデータに合った手法を選びましょう:
          </p>

          <div className="space-y-4">
            {/* Single table */}
            <div>
              <h3 className="text-sm font-semibold text-blue-800 mb-1 flex items-center gap-1.5">
                <span>&#x1F4CA;</span> 単一表データ（顧客マスタ等）
              </h3>
              <ul className="text-sm text-blue-900 space-y-1 ml-6">
                <li>
                  → まずは{" "}
                  <Link
                    to="/algorithm/gaussiancopula"
                    className="font-semibold text-blue-700 underline hover:text-blue-900"
                  >
                    GaussianCopula
                  </Link>{" "}
                  がおすすめ（高速・安定・チューニング不要）
                </li>
                <li>
                  → より高品質を求めるなら{" "}
                  <Link
                    to="/algorithm/ctgan"
                    className="font-semibold text-blue-700 underline hover:text-blue-900"
                  >
                    CTGAN
                  </Link>
                  （epochs=100 で Quality 86%）
                </li>
              </ul>
            </div>

            {/* Multi table */}
            <div>
              <h3 className="text-sm font-semibold text-blue-800 mb-1 flex items-center gap-1.5">
                <span>&#x1F517;</span> 複数表データ（マスタ + トランザクション）
              </h3>
              <ul className="text-sm text-blue-900 space-y-1 ml-6">
                <li>
                  →{" "}
                  <Link
                    to="/algorithm/hma"
                    className="font-semibold text-blue-700 underline hover:text-blue-900"
                  >
                    HMA
                  </Link>
                  （SDV）が唯一の対応手法。外部キー整合性を自動維持
                </li>
              </ul>
            </div>

            {/* Timeseries */}
            <div>
              <h3 className="text-sm font-semibold text-blue-800 mb-1 flex items-center gap-1.5">
                <span>&#x1F4C8;</span> 時系列データ（センサ・行動ログ等）
              </h3>
              <ul className="text-sm text-blue-900 space-y-1 ml-6">
                <li>
                  →{" "}
                  <Link
                    to="/algorithm/par"
                    className="font-semibold text-blue-700 underline hover:text-blue-900"
                  >
                    PAR
                  </Link>
                  （SDV）が対応。自己回帰モデルで時系列パターンを再現
                </li>
              </ul>
            </div>

            {/* Privacy */}
            <div>
              <h3 className="text-sm font-semibold text-blue-800 mb-1 flex items-center gap-1.5">
                <span>&#x1F512;</span> プライバシーを重視する場合
              </h3>
              <ul className="text-sm text-blue-900 space-y-1 ml-6">
                <li>
                  →{" "}
                  <Link
                    to="/algorithm/adsgan"
                    className="font-semibold text-blue-700 underline hover:text-blue-900"
                  >
                    AdsGAN
                  </Link>{" "}
                  はプライバシー考慮メカニズムを内蔵
                </li>
                <li>
                  → ただし「合成データ＝安全」ではないことに注意
                </li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
