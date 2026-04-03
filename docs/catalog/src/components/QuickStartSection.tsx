import { useState } from "react";

type LibraryCode = {
  install: string;
  code: string;
};

type AlgorithmCodeMap = {
  [library: string]: LibraryCode | undefined;
};

function getSdvImportPath(algorithmId: string): string {
  switch (algorithmId) {
    case "hma":
      return "sdv.multi_table";
    case "par":
      return "sdv.sequential";
    default:
      return "sdv.single_table";
  }
}

function getSdvClassName(algorithmId: string): string | null {
  switch (algorithmId) {
    case "gaussiancopula":
      return "GaussianCopulaSynthesizer";
    case "ctgan":
      return "CTGANSynthesizer";
    case "hma":
      return "HMASynthesizer";
    case "par":
      return "PARSynthesizer";
    default:
      return null;
  }
}

function getSdvParams(algorithmId: string): string {
  switch (algorithmId) {
    case "ctgan":
      return "metadata, epochs=100";
    default:
      return "metadata";
  }
}

function getSdvFitGenerate(algorithmId: string): string {
  if (algorithmId === "hma") {
    return `# 複数テーブルのメタデータを設定
metadata = Metadata.detect_from_dataframes(tables)

# 学習と生成
synthesizer = HMASynthesizer(metadata)
synthesizer.fit(tables)
synthetic_data = synthesizer.sample()`;
  }
  if (algorithmId === "par") {
    return `# 時系列メタデータの設定
metadata = Metadata.detect_from_dataframe(real_data)

# 学習と生成
synthesizer = PARSynthesizer(metadata)
synthesizer.fit(real_data)
synthetic_data = synthesizer.sample(num_sequences=100)`;
  }
  return `# メタデータの自動検出
metadata = Metadata.detect_from_dataframe(real_data)

# 学習と生成
synthesizer = ${getSdvClassName(algorithmId)}(${getSdvParams(algorithmId)})
synthesizer.fit(real_data)
synthetic_data = synthesizer.sample(num_rows=1000)`;
}

function getSynthCityPluginName(algorithmId: string): string | null {
  switch (algorithmId) {
    case "ctgan":
      return "ctgan";
    case "tvae":
      return "tvae";
    case "bayesian_network":
      return "bayesian_network";
    case "adsgan":
      return "adsgan";
    case "nflow":
      return "nflow";
    default:
      return null;
  }
}

function getCodeMap(algorithmId: string): AlgorithmCodeMap {
  const map: AlgorithmCodeMap = {};

  // SDV
  const sdvClass = getSdvClassName(algorithmId);
  if (sdvClass) {
    const importPath = getSdvImportPath(algorithmId);
    map["SDV"] = {
      install: "pip install sdv",
      code: `from ${importPath} import ${sdvClass}
from sdv.metadata import Metadata

${getSdvFitGenerate(algorithmId)}`,
    };
  }

  // SynthCity
  const synthCityPlugin = getSynthCityPluginName(algorithmId);
  if (synthCityPlugin) {
    map["SynthCity"] = {
      install: "pip install synthcity",
      code: `from synthcity.plugins import Plugins
from synthcity.plugins.core.dataloader import GenericDataLoader

loader = GenericDataLoader(real_data)
plugin = Plugins().get("${synthCityPlugin}")
plugin.fit(loader)
synthetic_data = plugin.generate(count=1000).dataframe()`,
    };
  }

  // ydata
  if (algorithmId === "ctgan") {
    map["ydata-synthetic"] = {
      install: "pip install ydata-synthetic",
      code: `from ydata_synthetic.synthesizers.regular import RegularSynthesizer
from ydata_synthetic.synthesizers import ModelParameters, TrainParameters

synth = RegularSynthesizer(modelname='ctgan', model_parameters=ModelParameters(batch_size=500))
synth.fit(data=real_data, train_arguments=TrainParameters(epochs=100), num_cols=num_cols, cat_cols=cat_cols)
synthetic_data = synth.sample(1000)`,
    };
  }

  return map;
}

function CodeBlock({ code, label }: { code: string; label: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="mb-3">
      <div className="flex items-center justify-between bg-gray-800 rounded-t-lg px-4 py-1.5">
        <span className="text-xs text-gray-400">{label}</span>
        <button
          onClick={handleCopy}
          className="text-xs text-gray-400 hover:text-white transition-colors px-2 py-0.5 rounded"
        >
          {copied ? "コピーしました!" : "コピー"}
        </button>
      </div>
      <pre className="bg-gray-900 text-green-400 rounded-b-lg p-4 overflow-x-auto text-sm leading-relaxed">
        <code>{code}</code>
      </pre>
    </div>
  );
}

type Props = {
  libraries: string[];
  algorithmId: string;
};

export function QuickStartSection({ libraries, algorithmId }: Props) {
  const codeMap = getCodeMap(algorithmId);
  const availableLibraries = libraries.filter((lib) => codeMap[lib]);
  const [activeTab, setActiveTab] = useState(availableLibraries[0] ?? "");
  const [isOpen, setIsOpen] = useState(true);

  if (availableLibraries.length === 0) {
    return null;
  }

  const activeCode = codeMap[activeTab];

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between text-left"
      >
        <h2 className="font-semibold text-gray-800 text-lg flex items-center gap-2">
          <span>&#9889;</span> クイックスタート
        </h2>
        <span className="text-gray-400 text-sm">
          {isOpen ? "▲ 閉じる" : "▼ 開く"}
        </span>
      </button>

      {isOpen && (
        <div className="mt-4">
          {/* Library tabs */}
          {availableLibraries.length > 1 && (
            <div className="flex gap-1 mb-4 border-b border-gray-200">
              {availableLibraries.map((lib) => (
                <button
                  key={lib}
                  onClick={() => setActiveTab(lib)}
                  className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
                    activeTab === lib
                      ? "bg-gray-900 text-green-400"
                      : "text-gray-600 hover:text-gray-800 hover:bg-gray-100"
                  }`}
                >
                  {lib}
                </button>
              ))}
            </div>
          )}

          {activeCode && (
            <>
              <CodeBlock code={activeCode.install} label="インストール" />
              <CodeBlock code={activeCode.code} label="サンプルコード" />
            </>
          )}
        </div>
      )}
    </div>
  );
}
