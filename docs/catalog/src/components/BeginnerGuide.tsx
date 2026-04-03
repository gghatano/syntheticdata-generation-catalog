import { useState } from "react";
import { Link } from "react-router-dom";

export function BeginnerGuide() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="mb-6">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between bg-blue-50 border border-blue-200 px-5 py-3 text-left hover:bg-blue-100 transition-colors"
        style={{
          borderRadius: isOpen ? "0.5rem 0.5rem 0 0" : "0.5rem",
        }}
      >
        <span className="font-semibold text-blue-800 flex items-center gap-2">
          <span>&#x1F530;</span> 初めての方へ：合成データ生成を試してみたい方に
        </span>
        <span className="text-blue-400 text-sm shrink-0 ml-2">
          {isOpen ? "▲ 閉じる" : "▼ 開く"}
        </span>
      </button>

      {isOpen && (
        <div className="bg-blue-50 border border-t-0 border-blue-200 rounded-b-lg px-5 py-4 border-l-4 border-l-blue-400">
          <p className="text-sm text-blue-900 mb-4">
            どんなデータを合成したいですか？ 実際の実験例を参考に手法を選んでみましょう。
          </p>

          <div className="space-y-5">
            {/* Single table */}
            <div className="bg-white/60 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-blue-800 mb-2 flex items-center gap-1.5">
                <span>&#x1F4CA;</span> 単一表データ（顧客マスタ・個人属性テーブル等）
              </h3>
              <div className="text-sm text-gray-700 mb-2 ml-1">
                <span className="text-gray-500">実験例:</span>{" "}
                Adult Census データ（32,561行 × 15列：年齢・職業・学歴・収入等）を合成
              </div>
              <div className="space-y-2 ml-1">
                <div className="flex items-start gap-2">
                  <span className="text-green-600 mt-0.5 shrink-0">▶</span>
                  <div>
                    <span className="text-gray-600">まずは試すなら → </span>
                    <Link
                      to="/algorithm/gaussiancopula"
                      className="font-semibold text-blue-700 underline hover:text-blue-900"
                    >
                      GaussianCopula
                    </Link>
                    <span className="text-gray-500 text-xs ml-2">
                      6秒で完了。統計的手法でチューニング不要。Quality 82%
                    </span>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <span className="text-green-600 mt-0.5 shrink-0">▶</span>
                  <div>
                    <span className="text-gray-600">より高品質なら → </span>
                    <Link
                      to="/algorithm/ctgan"
                      className="font-semibold text-blue-700 underline hover:text-blue-900"
                    >
                      CTGAN
                    </Link>
                    <span className="text-gray-500 text-xs ml-2">
                      深層学習で複雑な分布も再現。100epochs で Quality 86%（約5分）
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Multi table */}
            <div className="bg-white/60 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-blue-800 mb-2 flex items-center gap-1.5">
                <span>&#x1F517;</span> 複数表データ（マスタ + トランザクション）
              </h3>
              <div className="text-sm text-gray-700 mb-2 ml-1">
                <span className="text-gray-500">実験例:</span>{" "}
                ホテル予約データ（hotels: 10件 + guests: 658件）を外部キー関係を維持して合成
              </div>
              <div className="ml-1">
                <div className="flex items-start gap-2">
                  <span className="text-green-600 mt-0.5 shrink-0">▶</span>
                  <div>
                    <Link
                      to="/algorithm/hma"
                      className="font-semibold text-blue-700 underline hover:text-blue-900"
                    >
                      HMA
                    </Link>
                    <span className="text-gray-600">（SDV）</span>
                    <span className="text-gray-500 text-xs ml-2">
                      親子テーブルの外部キー整合性を自動維持。約5秒で完了
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Timeseries */}
            <div className="bg-white/60 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-blue-800 mb-2 flex items-center gap-1.5">
                <span>&#x1F4C8;</span> 時系列データ（センサ・行動ログ・株価等）
              </h3>
              <div className="text-sm text-gray-700 mb-2 ml-1">
                <span className="text-gray-500">実験例:</span>{" "}
                NASDAQ 100 株価データ（25,784行 × 8列：日次株価の時系列）を銘柄単位で合成
              </div>
              <div className="ml-1">
                <div className="flex items-start gap-2">
                  <span className="text-green-600 mt-0.5 shrink-0">▶</span>
                  <div>
                    <Link
                      to="/algorithm/par"
                      className="font-semibold text-blue-700 underline hover:text-blue-900"
                    >
                      PAR
                    </Link>
                    <span className="text-gray-600">（SDV）</span>
                    <span className="text-gray-500 text-xs ml-2">
                      自己回帰モデルで時系列パターンを再現。約2分で完了
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Privacy */}
            <div className="bg-amber-50/80 rounded-lg p-4 border border-amber-200">
              <h3 className="text-sm font-semibold text-amber-800 mb-2 flex items-center gap-1.5">
                <span>&#x1F512;</span> プライバシーを重視する場合
              </h3>
              <div className="space-y-1 ml-1">
                <div className="flex items-start gap-2">
                  <span className="text-amber-600 mt-0.5 shrink-0">▶</span>
                  <div>
                    <Link
                      to="/algorithm/adsgan"
                      className="font-semibold text-amber-700 underline hover:text-amber-900"
                    >
                      AdsGAN
                    </Link>
                    <span className="text-gray-500 text-xs ml-2">
                      学習時にプライバシー考慮メカニズムを適用するGAN
                    </span>
                  </div>
                </div>
                <p className="text-xs text-amber-700 mt-2">
                  ※ 合成データ＝匿名データではありません。利用前にプライバシー評価を推奨します
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
