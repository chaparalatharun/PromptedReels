// src/components/NewProjectModal.tsx
import { useEffect, useState } from "react";
import Modal from "./Modal";

export type NewProjectPayload = {
  project_name: string;
  script_idea: string;
  clip_style?: string;   
  duration?: number;
};

type Props = {
  open: boolean;
  onClose: () => void;
  onCreate: (payload: NewProjectPayload) => void | Promise<void>;
  submitting?: boolean;
  initial?: Partial<NewProjectPayload>;
};

const PRESET_STYLES = ["Explainer", "Listicle", "Story", "Promo"] as const;
const DURATIONS = [15, 30, 45, 60];

export default function NewProjectModal({
  open,
  onClose,
  onCreate,
  submitting = false,
  initial = {},
}: Props) {
  const [form, setForm] = useState<NewProjectPayload>({
    project_name: "",
    script_idea: "",
    clip_style: "",
    duration: undefined,
    ...initial,
  });

  // Reset when opened
  useEffect(() => {
    if (open) {
      setForm({
        project_name: initial.project_name ?? "",
        script_idea: initial.script_idea ?? "",
        clip_style: initial.clip_style ?? "",
        duration: initial.duration,
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const canSubmit =
    form.project_name.trim().length > 0 &&
    form.script_idea.trim().length > 0 &&
    !submitting;

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Create a new project"
      footer={
        <>
          <button onClick={onClose} className="px-3 py-2 rounded-lg border">
            Cancel
          </button>
          <button
            onClick={() => onCreate(form)}
            disabled={!canSubmit}
            className="px-3 py-2 rounded-lg bg-slate-900 text-white disabled:opacity-60"
          >
            {submitting ? "Creating…" : "Create"}
          </button>
        </>
      }
    >
      <div className="grid gap-3">
        {/* Project name */}
        <div className="grid gap-1.5">
          <label className="text-sm font-medium text-slate-700">Project name</label>
          <input
            className="border rounded-lg px-3 py-2"
            placeholder="e.g., sheep-story"
            value={form.project_name}
            onChange={(e) => setForm({ ...form, project_name: e.target.value })}
          />
        </div>

        {/* Script idea */}
        <div className="grid gap-1.5">
          <label className="text-sm font-medium text-slate-700">Script idea</label>
          <textarea
            className="border rounded-lg px-3 py-2 h-28"
            placeholder={
              "Paste a paragraph, a few lines, or a rough idea.\nWe'll structure it into concise blocks for a 9:16 short."
            }
            value={form.script_idea}
            onChange={(e) => setForm({ ...form, script_idea: e.target.value })}
          />
        </div>

        {/* Optional: Clip style (free text + quick presets) */}
        <div className="grid gap-1.5">
          <label className="text-sm font-medium text-slate-700">
            Clip style <span className="text-slate-400 font-normal">(optional)</span>
          </label>
          <input
            className="border rounded-lg px-3 py-2"
            placeholder='e.g., Explainer, Listicle, "Fast-cut meme", "Calm tutorial"'
            value={form.clip_style ?? ""}
            onChange={(e) => setForm({ ...form, clip_style: e.target.value })}
          />
          <div className="flex flex-wrap gap-2 pt-1">
            {PRESET_STYLES.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => setForm({ ...form, clip_style: s })}
                className="px-3 py-1.5 rounded-lg text-sm border hover:bg-slate-50"
              >
                {s}
              </button>
            ))}
            {form.clip_style ? (
              <button
                type="button"
                onClick={() => setForm({ ...form, clip_style: "" })}
                className="px-3 py-1.5 rounded-lg text-sm border hover:bg-slate-50"
                title="Clear style"
              >
                Clear
              </button>
            ) : null}
          </div>
        </div>

        {/* Optional: Duration */}
        <div className="grid gap-1.5">
          <label className="text-sm font-medium text-slate-700">
            Duration <span className="text-slate-400 font-normal">(optional)</span>
          </label>
          <div className="flex flex-wrap gap-2">
            {DURATIONS.map((d) => {
              const active = form.duration === d;
              return (
                <button
                  key={d}
                  type="button"
                  onClick={() =>
                    setForm({ ...form, duration: active ? undefined : d })
                  }
                  className={
                    "px-3 py-1.5 rounded-lg text-sm border " +
                    (active ? "bg-slate-900 text-white" : "hover:bg-slate-50")
                  }
                >
                  {d}s
                </button>
              );
            })}
            {/* Freeform input */}
            <div className="flex items-center gap-2">
              <input
                type="number"
                min={5}
                max={180}
                placeholder="Custom"
                value={form.duration ?? ""}
                onChange={(e) =>
                  setForm({
                    ...form,
                    duration: e.target.value ? Number(e.target.value) : undefined,
                  })
                }
                className="w-24 border rounded-lg px-2 py-1.5"
              />
              <span className="text-sm text-slate-500">sec</span>
            </div>
          </div>
        </div>
      </div>
    </Modal>
  );
}