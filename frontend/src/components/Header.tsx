import { Link } from "react-router-dom";

function LogoMark() {
  return (
    <div className="inline-grid place-items-center w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-600 to-blue-500 text-white font-bold">
      P
    </div>
  );
}

export default function Header() {
  return (
    <header className="sticky top-0 z-40 border-b bg-white/80 backdrop-blur supports-[backdrop-filter]:bg-white/60">
      <div className="mx-auto max-w-6xl px-4 h-14 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2">
          <LogoMark />
          <span className="font-semibold tracking-tight">Prompted Reels</span>
        </Link>
        <nav className="text-sm text-slate-600">
          <Link to="/" className="hover:text-slate-900">
            Home
          </Link>
        </nav>
      </div>
    </header>
  );
}