import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listProjects, createProject, generateMedia } from "../lib/api";
import ProjectCard from "../components/ProjectCard";
import NewProjectModal, { type NewProjectPayload } from "../components/NewProjectModal";

export default function Home() {
  const nav = useNavigate();
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);

  const { data: projects, isLoading } = useQuery({
    queryKey: ["projects"],
    queryFn: listProjects,
  });

  const createMut = useMutation({
    mutationFn: (payload: NewProjectPayload) => {
      const request = {
        project_name: payload.project_name,
        script_idea: payload.script_idea,
        style: payload.clip_style ?? "",
        target_seconds: payload.duration ?? 30,
      };
      return createProject(request);
    },
    onSuccess: () => {
      setOpen(false);
      qc.invalidateQueries({ queryKey: ["projects"] });
    },
  });

  const genMut = useMutation({
    mutationFn: (name: string) => generateMedia(name),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["projects"] }),
  });

  return (
    <div className="space-y-16">
      {/* HERO */}
      <section className="relative overflow-hidden rounded-2xl border bg-white px-6 py-20 sm:px-12">
        <div className="pointer-events-none absolute -top-24 -left-20 h-72 w-72 rounded-full bg-indigo-200/40 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-24 -right-24 h-72 w-72 rounded-full bg-sky-200/40 blur-3xl" />
        <div className="relative">
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-slate-900">
            From prompt to reel.{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-blue-600">
              Generate faceless stories.
            </span>
          </h1>
          <p className="mt-4 max-w-2xl text-lg text-slate-600">
            Write your script, choose a voice, and watch your idea turn into a short video — without recording or editing.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <button
              onClick={() => setOpen(true)}
              className="px-5 py-2.5 rounded-xl bg-slate-900 text-white hover:bg-slate-800"
            >
              Start Creating
            </button>
          </div>
        </div>
      </section>

      {/* PROJECTS */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-slate-800">Your Projects</h2>
        </div>

        {isLoading ? (
          <div className="text-slate-500">Loading your workspace…</div>
        ) : projects?.length ? (
          <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
            {projects.map((name: string) => (
              <ProjectCard
                key={name}
                name={name}
                onOpen={() => nav(`/p/${encodeURIComponent(name)}`)}
                onGenerate={() => genMut.mutate(name)}
              />
            ))}
          </div>
        ) : (
          <div className="rounded-xl border bg-white p-6 text-slate-600 text-center">
            You don’t have any projects yet. <br />
            Click <span className="font-medium text-slate-900">Start Creating</span> to turn your first idea into a reel.
          </div>
        )}
      </section>

      {/* CREATE MODAL */}
      <NewProjectModal
        open={open}
        onClose={() => setOpen(false)}
        submitting={createMut.isPending}
        onCreate={(payload) => createMut.mutate(payload)}
      />
    </div>
  );
}