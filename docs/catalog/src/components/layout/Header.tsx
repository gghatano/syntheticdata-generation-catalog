export function Header() {
  return (
    <header className="bg-blue-600 text-white shadow-md">
      <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
        <h1 className="text-xl font-bold">
          <a href={import.meta.env.BASE_URL} className="hover:opacity-90">
            Synthetic Data Generation Catalog
          </a>
        </h1>
        <nav className="text-sm text-blue-100">
          <span>合成データ生成手法カタログ</span>
        </nav>
      </div>
    </header>
  );
}
