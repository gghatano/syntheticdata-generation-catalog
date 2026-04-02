import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Layout } from "./components/layout/Layout";
import { ListPage } from "./pages/ListPage";
import { DetailPage } from "./pages/DetailPage";

const basename = import.meta.env.BASE_URL;

function App() {
  return (
    <BrowserRouter basename={basename}>
      <Layout>
        <Routes>
          <Route path="/" element={<ListPage />} />
          <Route path="/algorithm/:id" element={<DetailPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
