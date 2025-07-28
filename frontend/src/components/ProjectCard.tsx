import { useNavigate } from "react-router-dom";

type Props = {
  name: string;
  onOpen?: () => void;
  onGenerate?: () => void;
};

export default function ProjectCard({ name, onOpen, onGenerate }: Props) {
  const nav = useNavigate();

  const handleOpen = () => {
    if (onOpen) {
      onOpen();
    } else {
      nav(`/p/${encodeURIComponent(name)}`);
    }
  };

  return (
    <div className="rounded-xl border bg-white p-4 shadow-sm ring-1 ring-black/5 hover:shadow-md transition">
      <div className="mb-3">
        <div className="text-sm text-slate-500">Project</div>
        <div className="font-medium text-slate-900 truncate">{name}</div>
      </div>
      <div className="flex gap-2">
        <button
          onClick={handleOpen}
          className="px-3 py-1.5 rounded-lg bg-slate-900 text-white text-sm hover:bg-slate-800"
        >
          Open
        </button>
      </div>
    </div>
  );
}