export interface HealthResponse {
  status: string;
  service: string;
  version?: string;
}

export interface NavItem {
  label: string;
  path: string;
  icon?: string;
}

export interface Department {
  id: string;
  name: string;
  created_at?: string;
}

export interface Skill {
  id: string;
  name: string;
  category: string;
  created_at?: string;
}

export interface Interest {
  id: string;
  name: string;
  created_at?: string;
}

export interface StudentProfile {
  id: string;
  user_id: string;
  full_name: string;
  department_id: string | null;
  academic_year: number;
  bio?: string | null;
  github_url?: string | null;
  linkedin_url?: string | null;
  portfolio_url?: string | null;
  hours_per_week?: number;
  created_at?: string;
  updated_at?: string;
}

export interface StudentProfileUpdate {
  full_name?: string;
  department_id?: string | null;
  academic_year?: number;
  bio?: string | null;
  github_url?: string | null;
  linkedin_url?: string | null;
  portfolio_url?: string | null;
  hours_per_week?: number;
}

export interface StudentSkill {
  id: string;
  student_id: string;
  skill_id: string;
  proficiency: number; // 1 to 4
  created_at?: string;
  skill_name?: string;
  category?: string;
}

export interface StudentInterest {
  id: string;
  student_id: string;
  interest_id: string;
  created_at?: string;
  interest_name?: string;
}

export interface Certification {
  id: string;
  student_id: string;
  name: string;
  issuing_organization: string;
  issue_date: string;
  credential_url?: string | null;
  created_at?: string;
}

export interface CertificationCreate {
  name: string;
  issuing_organization: string;
  issue_date: string;
  credential_url?: string | null;
}

export interface PreviousProject {
  id: string;
  student_id: string;
  title: string;
  description: string;
  technologies?: string[];
  project_url?: string | null;
  created_at?: string;
}

export interface PreviousProjectCreate {
  title: string;
  description: string;
  technologies?: string[];
  project_url?: string | null;
}

// ------------------------------------------------------------------------------
// Phase 4: Project Types
// ------------------------------------------------------------------------------

export type ProjectStatus = 'open' | 'in_progress' | 'completed' | 'archived';

export interface Project {
  id: string;
  owner_id: string;
  title: string;
  description: string;
  status: ProjectStatus;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  title: string;
  description: string;
  status?: 'open' | 'in_progress' | 'completed';
}

export interface ProjectUpdate {
  title?: string;
  description?: string;
  status?: ProjectStatus;
}

export interface ProjectSkill {
  id: string;
  project_id: string;
  skill_id: string;
  required_proficiency: number; // 1 to 4
  created_at: string;
  skill_name?: string;
  category?: string;
}

export interface ProjectMember {
  id: string;
  project_id: string;
  student_id: string;
  role: string;
  joined_at: string;
  student_name?: string;
}

export interface ProjectOwner {
  id: string;
  user_id: string;
  full_name: string;
  academic_year?: number;
}

export interface ProjectDetail {
  id: string;
  owner_id: string;
  title: string;
  description: string;
  status: ProjectStatus;
  created_at: string;
  updated_at: string;
  owner?: ProjectOwner;
  required_skills: ProjectSkill[];
  members: ProjectMember[];
}

// ------------------------------------------------------------------------------
// Phase 5: AI Project Analysis Types
// ------------------------------------------------------------------------------

export interface ExtractedSkill {
  skill_name: string;
  skill_id?: string | null;
  category?: string | null;
  confidence: number;
  source: string;
}

export interface ProjectAnalysisResult {
  project_id: string;
  normalized_description: string;
  embedding_available: boolean;
  embedding_dimension?: number | null;
  model_name?: string | null;
  extracted_skills: ExtractedSkill[];
  analysis_status: 'completed' | 'partial' | 'not_ready';
  warnings: string[];
}

// ------------------------------------------------------------------------------
// Phase 5 Step 4: Recommendation Types
// ------------------------------------------------------------------------------

export interface MatchedSkillInfo {
  skill_id: string;
  skill_name: string;
  student_proficiency: number;
  required_proficiency: number;
  category?: string | null;
}

export interface MissingSkillInfo {
  skill_id: string;
  skill_name: string;
  required_proficiency: number;
  category?: string | null;
}

export interface FactualExplanation {
  matched_skills: MatchedSkillInfo[];
  missing_skills: MissingSkillInfo[];
  skill_coverage_ratio: number;
  proficiency_alignment: number;
  interest_overlap: number;
  experience_signal: number;
}

export interface StudentRecommendation {
  rank: number;
  student_id: string;
  student_name: string;
  academic_year?: number | null;
  compatibility_score: number;
  matched_skill_count: number;
  required_skill_count: number;
  skill_coverage_ratio: number;
  mean_proficiency_matched: number;
  proficiency_deficit_ratio: number;
  interest_domain_overlap: number;
  prior_project_experience_norm: number;
  certification_count_norm: number;
  explanation: FactualExplanation;
  invitation_status?: 'pending' | 'accepted' | 'rejected' | 'cancelled' | null;
  invitation_id?: string | null;
}

export interface ProjectRecommendationResponse {
  project_id: string;
  project_title: string;
  total_eligible_candidates: number;
  returned_recommendations_count: number;
  min_score_threshold: number;
  model_version: string;
  recommendations: StudentRecommendation[];
}

// ------------------------------------------------------------------------------
// Phase 6: Skill-Gap Analysis Types
// ------------------------------------------------------------------------------

export type SkillGapStatus = 'matched' | 'partial' | 'missing';

export interface SkillGapItem {
  skill_id: string;
  skill_name: string;
  category?: string | null;
  required_proficiency: number;
  student_proficiency: number | null;
  status: SkillGapStatus;
  proficiency_gap?: number | null;
}

export interface SkillGapSummary {
  total_required_skills: number;
  matched_count: number;
  partial_count: number;
  missing_count: number;
  skill_coverage_ratio: number;
  proficiency_gap_count: number;
  overall_gap_summary: string;
}

export interface SkillGapResponse {
  project_id: string;
  project_title?: string | null;
  student_id: string;
  student_name?: string | null;
  summary: SkillGapSummary;
  skills: SkillGapItem[];
}

// ------------------------------------------------------------------------------
// Phase 13: Voluntary Team Formation & Invitation Types
// ------------------------------------------------------------------------------

export type InvitationStatus = 'pending' | 'accepted' | 'rejected' | 'cancelled';

export interface InvitationCreate {
  student_id: string;
}

export interface SafeStudentSummary {
  id: string;
  full_name: string;
  academic_year?: number | null;
  department?: string | null;
}

export interface SafeProjectSummary {
  id: string;
  title: string;
  description: string;
  status: string;
  owner_id: string;
}

export interface InvitationResponse {
  id: string;
  project_id: string;
  inviter_id: string;
  invited_student_id: string;
  status: InvitationStatus;
  created_at: string;
  updated_at?: string | null;
  responded_at?: string | null;
  project?: SafeProjectSummary | null;
  inviter?: SafeStudentSummary | null;
  invited_student?: SafeStudentSummary | null;
}

export interface ProjectTeamMemberResponse {
  id: string;
  project_id: string;
  student_id: string;
  role: 'owner' | 'member';
  joined_at: string;
  full_name: string;
  academic_year?: number | null;
  department?: string | null;
}

// ------------------------------------------------------------------------------
// Phase 14: Project Progress, Tasks & Collaboration Feedback Types
// ------------------------------------------------------------------------------

export type ProgressStatus = 'on_track' | 'at_risk' | 'delayed' | 'completed';
export type TaskStatus = 'todo' | 'in_progress' | 'completed' | 'blocked';
export type TaskPriority = 'low' | 'medium' | 'high' | 'urgent';
export type CollaborationQuality = 'exceptional' | 'good' | 'adequate' | 'challenging';

export interface ProjectTask {
  id: string;
  project_id: string;
  title: string;
  description?: string | null;
  assigned_student_id?: string | null;
  assigned_student_name?: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  due_date?: string | null;
  completed_at?: string | null;
  created_by: string;
  created_by_name?: string | null;
  created_at: string;
  updated_at?: string | null;
}

export interface ProjectTaskCreate {
  title: string;
  description?: string;
  assigned_student_id?: string | null;
  status?: TaskStatus;
  priority?: TaskPriority;
  due_date?: string | null;
}

export interface ProjectTaskUpdate {
  title?: string;
  description?: string;
  assigned_student_id?: string | null;
  status?: TaskStatus;
  priority?: TaskPriority;
  due_date?: string | null;
}

export interface ProjectProgress {
  id: string;
  project_id: string;
  title: string;
  description?: string | null;
  progress_percentage: number;
  status: ProgressStatus;
  created_by: string;
  created_by_name?: string | null;
  created_at: string;
  updated_at?: string | null;
  completed_at?: string | null;
}

export interface ProjectProgressCreate {
  title: string;
  description?: string;
  progress_percentage: number;
  status?: ProgressStatus;
}

export interface ProjectProgressUpdate {
  title?: string;
  description?: string;
  progress_percentage?: number;
  status?: ProgressStatus;
}

export interface ProjectProgressOverview {
  project_id: string;
  overall_progress_percentage: number;
  total_tasks: number;
  completed_tasks: number;
  in_progress_tasks: number;
  blocked_tasks: number;
  todo_tasks: number;
  latest_milestone_status: string;
  tasks: ProjectTask[];
  updates: ProjectProgress[];
}

export interface FeedbackCreate {
  rating: number; // 1-5
  feedback_text?: string;
  collaboration_quality?: CollaborationQuality;
  skills_aligned?: boolean;
}

export interface FeedbackResponse {
  id: string;
  project_id: string;
  student_id: string;
  student_name?: string | null;
  rating: number;
  feedback_text?: string | null;
  collaboration_quality?: CollaborationQuality | null;
  skills_aligned: boolean;
  created_at: string;
  updated_at?: string | null;
}

export interface FeedbackSummary {
  project_id: string;
  average_rating: number;
  total_feedback_count: number;
  skills_aligned_percentage: number;
  feedback_list: FeedbackResponse[];
}

