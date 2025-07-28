import axios from "axios";
const API_BASE = "/api";

export type CreateProjectRequest = {
  project_name: string;
  script_idea: string;
  style?: string;
  target_seconds?: number;
};

export async function listProjects(): Promise<string[]> {
  const { data } = await axios.get(`${API_BASE}/projects`);
  return data.projects?.map((p: { name: string }) => p.name) ?? [];
}

export async function createProject(payload: CreateProjectRequest) {
  const { data } = await axios.post(`${API_BASE}/projects/create`, payload);
  return data;
}

export async function generateMedia(project_name: string, style = "") {
  const { data } = await axios.post(`${API_BASE}/generate_media`, { project_name, style });
  return data;
}

export function staticUrl(path: string) {
  return `/static/${path}`;
}