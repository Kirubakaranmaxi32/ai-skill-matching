export interface StudentProfileCompleteness {
  with_skills: number;
  with_interests: number;
  with_previous_projects: number;
  with_certifications: number;
  completion_rate_percentage: number;
}

export interface SkillProficiencyDistribution {
  beginner: number;
  intermediate: number;
  advanced: number;
  expert: number;
}

export interface MostCommonSkill {
  skill_id: string;
  skill_name: string;
  category: string;
  student_count: number;
}

export interface ProjectSkillDemand {
  skill_id: string;
  skill_name: string;
  category: string;
  project_count: number;
}

export interface AdminStudentStats {
  total_students: number;
  students_by_department: Array<{ department: string; count: number }>;
  students_by_year: Record<string, number>;
  profile_completeness: StudentProfileCompleteness;
  total_skills: number;
  skills_by_category: Record<string, number>;
  most_common_skills: MostCommonSkill[];
  proficiency_distribution: SkillProficiencyDistribution;
  project_skill_demand: ProjectSkillDemand[];
  demo_mode: boolean;
}

export interface ProjectInvitationStats {
  total_invitations: number;
  invitations_by_status: Record<string, number>;
  acceptance_rate: number;
}

export interface RecentProject {
  id: string;
  title: string;
  status: string;
  owner_id: string;
  created_at: string;
}

export interface AdminProjectStats {
  total_projects: number;
  projects_by_status: Record<string, number>;
  recent_projects: RecentProject[];
  total_project_members: number;
  avg_team_size: number;
  max_team_size: number;
  invitation_stats: ProjectInvitationStats;
  demo_mode: boolean;
}

export interface AdminProgressStats {
  avg_project_progress: number;
  projects_by_progress_status: Record<string, number>;
  total_tasks: number;
  tasks_by_status: Record<string, number>;
  completed_tasks: number;
  pending_tasks: number;
  blocked_tasks: number;
  tasks_by_priority: Record<string, number>;
  demo_mode: boolean;
}

export interface RecentFeedback {
  id: string;
  project_id: string;
  student_id: string;
  rating: number | null;
  feedback_text: string | null;
  created_at: string;
}

export interface AdminFeedbackStats {
  total_feedback: number;
  avg_rating: number | null;
  rating_distribution: Record<string, number>;
  recent_feedback: RecentFeedback[];
  demo_mode: boolean;
}

export interface RecommendationReadiness {
  eligible_candidates_count: number;
  projects_with_skills_count: number;
}

export interface AdminAiMatchingStats {
  model_loaded: boolean;
  model_type: string;
  model_version: string;
  input_features_count: number;
  hidden_layers: number[];
  trainable_parameters: number;
  checkpoint_present: boolean;
  sentence_transformer_available: boolean;
  sentence_transformer_model: string;
  recommendation_readiness: RecommendationReadiness;
  feedback_satisfaction_avg: number | null;
  feedback_total_count: number;
  historical_tracking_available: boolean;
  historical_tracking_notice: string;
  demo_mode: boolean;
}

export interface AdminSystemStats {
  status: string;
  database_connected: boolean;
  database_mode: string;
  demo_mode: boolean;
  api_version: string;
  ai_subsystem_healthy: boolean;
  checkpoint_verified: boolean;
}

export interface AdminOverviewResponse {
  total_students: number;
  total_projects: number;
  total_project_members: number;
  total_invitations: number;
  avg_project_progress: number;
  total_feedback: number;
  avg_feedback_rating: number | null;
  ai_model_loaded: boolean;
  ai_model_version: string;
  database_connected: boolean;
  demo_mode: boolean;
}

export interface AdminStatusResponse {
  is_admin: boolean;
  user_id: string;
  email: string;
}
