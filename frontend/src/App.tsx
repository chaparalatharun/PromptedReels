import { Routes, Route } from "react-router-dom";
import Header from "./components/Header";
import Home from "./pages/Home";
import ProjectCanvasPage from "./pages/project/ProjectCanvasPage";

export default function App() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <Header />
      <main className="mx-auto max-w-6xl px-4 py-8">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/p/:name" element={<ProjectCanvasPage />} />
        </Routes>
      </main>
    </div>
  );
}