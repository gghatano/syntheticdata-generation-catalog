import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Layout } from "./components/layout/Layout";
import { ListPage } from "./pages/ListPage";
import { DetailPage } from "./pages/DetailPage";
import { CaseDetailPage } from "./pages/CaseDetailPage";

const basename = import.meta.env.BASE_URL;

function App() {
  return (
    <BrowserRouter basename={basename}>
      <Layout>
        <Routes>
          <Route path="/" element={<ListPage />} />
          <Route path="/algorithm/:id" element={<DetailPage />} />
          <Route path="/case/:id" element={<CaseDetailPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
