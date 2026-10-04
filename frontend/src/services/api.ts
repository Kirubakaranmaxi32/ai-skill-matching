import axios from 'axios';
import {
  HealthResponse,
  Department,
  Skill,
  Interest,
  StudentProfile,
  StudentProfileUpdate,
  StudentSkill,
  StudentInterest,
  Certification,
  CertificationCreate,
  PreviousProject,
  PreviousProjectCreate,
  Project,
  ProjectCreate,
  ProjectUpdate,
  ProjectSkill,
  ProjectDetail,
  ProjectAnalysisResult,
  ProjectRecommendationResponse,
  SkillGapResponse,
  InvitationResponse,
  InvitationStatus,
  ProjectProgressOverview,
  ProjectProgress,
  ProjectProgressCreate,
  ProjectProgressUpdate,
  ProjectTask,
  ProjectTaskCreate,
  ProjectTaskUpdate,
  FeedbackCreate,
  FeedbackResponse,
  FeedbackSummary,
} from '../types';
import { supabase, isSupabaseConfigured } from './supabase';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Request interceptor to automatically attach authenticated Supabase JWT
apiClient.interceptors.request.use(async (config) => {
  if (isSupabaseConfigured()) {
    try {
      const { data } = await supabase.auth.getSession();
      if (data?.session?.access_token) {
        config.headers.Authorization = `Bearer ${data.session.access_token}`;
      }
    } catch (err) {
      console.warn('Could not attach Supabase auth token to request:', err);
    }
  }
  return config;
});

// System Health Endpoints
export const checkRootHealth = async (): Promise<HealthResponse> => {
  const response = await axios.get<HealthResponse>(`${BACKEND_URL}/health`);
  return response.data;
};

export const checkV1Health = async (): Promise<HealthResponse> => {
  const response = await apiClient.get<HealthResponse>('/health');
  return response.data;
};

// Reference Data Endpoints
export const getDepartments = async (): Promise<Department[]> => {
  const response = await apiClient.get<Department[]>('/departments');
  return response.data;
};

export const getSkills = async (): Promise<Skill[]> => {
  const response = await apiClient.get<Skill[]>('/skills');
  return response.data;
};

export const getInterests = async (): Promise<Interest[]> => {
  const response = await apiClient.get<Interest[]>('/interests');
  return response.data;
};

// Student Profile Endpoints
export const getStudentProfile = async (): Promise<StudentProfile> => {
  const response = await apiClient.get<StudentProfile>('/students/me');
  return response.data;
};

export const updateStudentProfile = async (
  profile: StudentProfileUpdate
): Promise<StudentProfile> => {
  const response = await apiClient.put<StudentProfile>('/students/me', profile);
  return response.data;
};

// Student Skills Endpoints
export const getStudentSkills = async (): Promise<StudentSkill[]> => {
  const response = await apiClient.get<StudentSkill[]>('/students/me/skills');
  return response.data;
};

export const addStudentSkill = async (
  skill_id: string,
  proficiency: number
): Promise<StudentSkill> => {
  const response = await apiClient.post<StudentSkill>('/students/me/skills', {
    skill_id,
    proficiency,
  });
  return response.data;
};

export const deleteStudentSkill = async (skill_id: string): Promise<void> => {
  await apiClient.delete(`/students/me/skills/${skill_id}`);
};

// Student Interests Endpoints
export const getStudentInterests = async (): Promise<StudentInterest[]> => {
  const response = await apiClient.get<StudentInterest[]>('/students/me/interests');
  return response.data;
};

export const addStudentInterest = async (interest_id: string): Promise<StudentInterest> => {
  const response = await apiClient.post<StudentInterest>('/students/me/interests', {
    interest_id,
  });
  return response.data;
};

export const deleteStudentInterest = async (interest_id: string): Promise<void> => {
  await apiClient.delete(`/students/me/interests/${interest_id}`);
};

// Certifications Endpoints
export const getStudentCertifications = async (): Promise<Certification[]> => {
  const response = await apiClient.get<Certification[]>('/students/me/certifications');
  return response.data;
};

export const addStudentCertification = async (
  data: CertificationCreate
): Promise<Certification> => {
  const response = await apiClient.post<Certification>('/students/me/certifications', data);
  return response.data;
};

export const deleteStudentCertification = async (cert_id: string): Promise<void> => {
  await apiClient.delete(`/students/me/certifications/${cert_id}`);
};

// Previous Projects Endpoints
export const getStudentProjects = async (): Promise<PreviousProject[]> => {
  const response = await apiClient.get<PreviousProject[]>('/students/me/projects');
  return response.data;
};

export const addStudentProject = async (
  data: PreviousProjectCreate
): Promise<PreviousProject> => {
  const response = await apiClient.post<PreviousProject>('/students/me/projects', data);
  return response.data;
};

export const deleteStudentProject = async (project_id: string): Promise<void> => {
  await apiClient.delete(`/students/me/projects/${project_id}`);
};

// ------------------------------------------------------------------------------
// Phase 4: Projects Endpoints
// ------------------------------------------------------------------------------

export const getMyProjects = async (): Promise<Project[]> => {
  const response = await apiClient.get<Project[]>('/projects/me');
  return response.data;
};

export const getProjects = async (scope: 'discover' | 'joined' | 'me' = 'discover'): Promise<Project[]> => {
  const response = await apiClient.get<Project[]>(`/projects?scope=${scope}`);
  return response.data;
};

export const createProject = async (data: ProjectCreate): Promise<Project> => {
  const response = await apiClient.post<Project>('/projects', data);
  return response.data;
};

export const getProjectById = async (projectId: string): Promise<ProjectDetail> => {
  const response = await apiClient.get<ProjectDetail>(`/projects/${projectId}`);
  return response.data;
};

export const updateProject = async (
  projectId: string,
  data: ProjectUpdate
): Promise<Project> => {
  const response = await apiClient.put<Project>(`/projects/${projectId}`, data);
  return response.data;
};

export const archiveProject = async (projectId: string): Promise<Project> => {
  const response = await apiClient.post<Project>(`/projects/${projectId}/archive`);
  return response.data;
};

export const getProjectSkills = async (projectId: string): Promise<ProjectSkill[]> => {
  const response = await apiClient.get<ProjectSkill[]>(`/projects/${projectId}/skills`);
  return response.data;
};

export const addProjectSkill = async (
  projectId: string,
  skillId: string,
  requiredProficiency: number
): Promise<ProjectSkill> => {
  const response = await apiClient.post<ProjectSkill>(`/projects/${projectId}/skills`, {
    skill_id: skillId,
    required_proficiency: requiredProficiency,
  });
  return response.data;
};

export const deleteProjectSkill = async (
  projectId: string,
  skillId: string
): Promise<void> => {
  await apiClient.delete(`/projects/${projectId}/skills/${skillId}`);
};

// ------------------------------------------------------------------------------
// Phase 5: Project AI Analysis
// ------------------------------------------------------------------------------

export const analyzeProject = async (projectId: string): Promise<ProjectAnalysisResult> => {
  const response = await apiClient.post<ProjectAnalysisResult>(`/projects/${projectId}/analyze`);
  return response.data;
};

export const getProjectRecommendations = async (
  projectId: string,
  topK: number = 10,
  minScore: number = 0.0
): Promise<ProjectRecommendationResponse> => {
  const response = await apiClient.get<ProjectRecommendationResponse>(
    `/projects/${projectId}/recommendations?top_k=${topK}&min_score=${minScore}`
  );
  return response.data;
};

// ------------------------------------------------------------------------------
// Phase 5: Demo Mode Endpoints
// ------------------------------------------------------------------------------

export interface DemoStatusResponse {
  demo_mode_configured: boolean;
  dataset_type: string;
  synthetic: boolean;
  source: string;
  description: string;
}

export const getDemoStatus = async (): Promise<DemoStatusResponse> => {
  const response = await apiClient.get<DemoStatusResponse>('/demo/status');
  return response.data;
};

export const getDemoProjects = async (): Promise<Project[]> => {
  const response = await apiClient.get<Project[]>('/demo/projects');
  return response.data;
};

export const getDemoProject = async (projectId: string): Promise<ProjectDetail> => {
  const response = await apiClient.get<ProjectDetail>(`/demo/projects/${projectId}`);
  return response.data;
};

export const getDemoRecommendations = async (
  projectId: string,
  topK: number = 10,
  minScore: number = 0.0
): Promise<ProjectRecommendationResponse> => {
  const response = await apiClient.get<ProjectRecommendationResponse>(
    `/demo/projects/${projectId}/recommendations?top_k=${topK}&min_score=${minScore}`
  );
  return response.data;
};

// ------------------------------------------------------------------------------
// Phase 6: Skill-Gap Analysis Endpoints
// ------------------------------------------------------------------------------

export const getProjectSkillGap = async (
  projectId: string,
  studentId?: string
): Promise<SkillGapResponse> => {
  const url = studentId
    ? `/projects/${projectId}/skill-gap?student_id=${studentId}`
    : `/projects/${projectId}/skill-gap`;
  const response = await apiClient.get<SkillGapResponse>(url);
  return response.data;
};

export const getDemoProjectSkillGap = async (
  projectId: string,
  studentId?: string
): Promise<SkillGapResponse> => {
  const url = studentId
    ? `/demo/projects/${projectId}/skill-gap?student_id=${studentId}`
    : `/demo/projects/${projectId}/skill-gap`;
  const response = await apiClient.get<SkillGapResponse>(url);
  return response.data;
};

// ------------------------------------------------------------------------------
// Phase 13: Voluntary Team Formation & Invitation Endpoints
// ------------------------------------------------------------------------------

export const getMyInvitations = async (
  status?: InvitationStatus,
  role: 'received' | 'sent' = 'received'
): Promise<InvitationResponse[]> => {
  const params = new URLSearchParams();
  if (status) params.append('status', status);
  params.append('role', role);
  const response = await apiClient.get<InvitationResponse[]>(`/invitations?${params.toString()}`);
  return response.data;
};

export const sendProjectInvitation = async (
  projectId: string,
  studentId: string
): Promise<InvitationResponse> => {
  const response = await apiClient.post<InvitationResponse>(`/projects/${projectId}/invitations`, {
    student_id: studentId,
  });
  return response.data;
};

export const getProjectInvitations = async (
  projectId: string
): Promise<InvitationResponse[]> => {
  const response = await apiClient.get<InvitationResponse[]>(`/projects/${projectId}/invitations`);
  return response.data;
};

export const acceptInvitation = async (
  invitationId: string
): Promise<InvitationResponse> => {
  const response = await apiClient.post<InvitationResponse>(`/invitations/${invitationId}/accept`);
  return response.data;
};

export const rejectInvitation = async (
  invitationId: string
): Promise<InvitationResponse> => {
  const response = await apiClient.post<InvitationResponse>(`/invitations/${invitationId}/reject`);
  return response.data;
};

export const cancelInvitation = async (
  invitationId: string
): Promise<InvitationResponse> => {
  const response = await apiClient.post<InvitationResponse>(`/invitations/${invitationId}/cancel`);
  return response.data;
};

// ------------------------------------------------------------------------------
// Phase 14: Project Progress, Tasks & Collaboration Feedback API
// ------------------------------------------------------------------------------

export const getProjectProgressOverview = async (
  projectId: string,
  isDemo: boolean = false
): Promise<ProjectProgressOverview> => {
  const isDemoProject = isDemo || projectId.startsWith('00000000-de00');
  const url = isDemoProject ? `/demo/projects/${projectId}/progress` : `/projects/${projectId}/progress`;
  const response = await apiClient.get<ProjectProgressOverview>(url);
  return response.data;
};

export const createProjectProgress = async (
  projectId: string,
  data: ProjectProgressCreate,
  isDemo: boolean = false
): Promise<ProjectProgress> => {
  const isDemoProject = isDemo || projectId.startsWith('00000000-de00');
  const url = isDemoProject ? `/demo/projects/${projectId}/progress` : `/projects/${projectId}/progress`;
  const response = await apiClient.post<ProjectProgress>(url, data);
  return response.data;
};

export const updateProjectProgress = async (
  projectId: string,
  progressId: string,
  data: ProjectProgressUpdate
): Promise<ProjectProgress> => {
  const response = await apiClient.patch<ProjectProgress>(
    `/projects/${projectId}/progress/${progressId}`,
    data
  );
  return response.data;
};

export const deleteProjectProgress = async (
  projectId: string,
  progressId: string
): Promise<{ status: string; message: string }> => {
  const response = await apiClient.delete<{ status: string; message: string }>(
    `/projects/${projectId}/progress/${progressId}`
  );
  return response.data;
};

export const getProjectTasks = async (
  projectId: string,
  isDemo: boolean = false
): Promise<ProjectTask[]> => {
  const isDemoProject = isDemo || projectId.startsWith('00000000-de00');
  const url = isDemoProject ? `/demo/projects/${projectId}/tasks` : `/projects/${projectId}/tasks`;
  const response = await apiClient.get<ProjectTask[]>(url);
  return response.data;
};

export const createProjectTask = async (
  projectId: string,
  data: ProjectTaskCreate,
  isDemo: boolean = false
): Promise<ProjectTask> => {
  const isDemoProject = isDemo || projectId.startsWith('00000000-de00');
  const url = isDemoProject ? `/demo/projects/${projectId}/tasks` : `/projects/${projectId}/tasks`;
  const response = await apiClient.post<ProjectTask>(url, data);
  return response.data;
};

export const updateProjectTask = async (
  projectId: string,
  taskId: string,
  data: ProjectTaskUpdate,
  isDemo: boolean = false
): Promise<ProjectTask> => {
  const isDemoProject = isDemo || projectId.startsWith('00000000-de00');
  const url = isDemoProject
    ? `/demo/projects/${projectId}/tasks/${taskId}`
    : `/projects/${projectId}/tasks/${taskId}`;
  const response = await apiClient.patch<ProjectTask>(url, data);
  return response.data;
};

export const deleteProjectTask = async (
  projectId: string,
  taskId: string,
  isDemo: boolean = false
): Promise<{ status: string; message: string }> => {
  const isDemoProject = isDemo || projectId.startsWith('00000000-de00');
  const url = isDemoProject
    ? `/demo/projects/${projectId}/tasks/${taskId}`
    : `/projects/${projectId}/tasks/${taskId}`;
  const response = await apiClient.delete<{ status: string; message: string }>(url);
  return response.data;
};

export const getProjectFeedback = async (
  projectId: string,
  isDemo: boolean = false
): Promise<FeedbackSummary> => {
  const isDemoProject = isDemo || projectId.startsWith('00000000-de00');
  const url = isDemoProject ? `/demo/projects/${projectId}/feedback` : `/projects/${projectId}/feedback`;
  const response = await apiClient.get<FeedbackSummary>(url);
  return response.data;
};

export const submitProjectFeedback = async (
  projectId: string,
  data: FeedbackCreate,
  isDemo: boolean = false
): Promise<FeedbackResponse> => {
  const isDemoProject = isDemo || projectId.startsWith('00000000-de00');
  const url = isDemoProject ? `/demo/projects/${projectId}/feedback` : `/projects/${projectId}/feedback`;
  const response = await apiClient.post<FeedbackResponse>(url, data);
  return response.data;
};


