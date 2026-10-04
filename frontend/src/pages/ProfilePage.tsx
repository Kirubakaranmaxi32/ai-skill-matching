import React, { useEffect, useState, useMemo } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  getStudentProfile,
  updateStudentProfile,
  getDepartments,
  getSkills,
  getInterests,
  getStudentSkills,
  addStudentSkill,
  deleteStudentSkill,
  getStudentInterests,
  addStudentInterest,
  deleteStudentInterest,
  getStudentCertifications,
  addStudentCertification,
  deleteStudentCertification,
  getStudentProjects,
  addStudentProject,
  deleteStudentProject,
} from '../services/api';
import {
  Department,
  Skill,
  Interest,
  StudentProfile,
  StudentSkill,
  StudentInterest,
  Certification,
  PreviousProject,
} from '../types';
import {
  User,
  GraduationCap,
  Award,
  Briefcase,
  Code,
  Sparkles,
  Plus,
  Trash2,
  ExternalLink,
  AlertCircle,
  CheckCircle2,
  Loader2,
  Search,
  Save,
  Building,
  Calendar,
  X,
} from 'lucide-react';

export const ProfilePage: React.FC = () => {
  const { user } = useAuth();

  // Reference state
  const [departments, setDepartments] = useState<Department[]>([]);
  const [availableSkills, setAvailableSkills] = useState<Skill[]>([]);
  const [availableInterests, setAvailableInterests] = useState<Interest[]>([]);

  // Student state
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [skills, setSkills] = useState<StudentSkill[]>([]);
  const [interests, setInterests] = useState<StudentInterest[]>([]);
  const [certifications, setCertifications] = useState<Certification[]>([]);
  const [projects, setProjects] = useState<PreviousProject[]>([]);

  // Page level loading & errors
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Active section tab
  const [activeTab, setActiveTab] = useState<'profile' | 'skills' | 'interests' | 'certifications' | 'projects'>('profile');

  // Form states: Personal Profile
  const [fullName, setFullName] = useState<string>('');
  const [departmentId, setDepartmentId] = useState<string>('');
  const [academicYear, setAcademicYear] = useState<number>(1);
  const [bio, setBio] = useState<string>('');
  const [githubUrl, setGithubUrl] = useState<string>('');
  const [linkedinUrl, setLinkedinUrl] = useState<string>('');
  const [portfolioUrl, setPortfolioUrl] = useState<string>('');
  const [hoursPerWeek, setHoursPerWeek] = useState<number>(10);
  const [savingProfile, setSavingProfile] = useState<boolean>(false);

  // Form states: Add Skill
  const [selectedSkillId, setSelectedSkillId] = useState<string>('');
  const [skillProficiency, setSkillProficiency] = useState<number>(3);
  const [skillSearchQuery, setSkillSearchQuery] = useState<string>('');
  const [addingSkill, setAddingSkill] = useState<boolean>(false);
  const [deletingSkillId, setDeletingSkillId] = useState<string | null>(null);

  // Form states: Add Interest
  const [selectedInterestId, setSelectedInterestId] = useState<string>('');
  const [interestSearchQuery, setInterestSearchQuery] = useState<string>('');
  const [addingInterest, setAddingInterest] = useState<boolean>(false);
  const [deletingInterestId, setDeletingInterestId] = useState<string | null>(null);

  // Form states: Add Certification
  const [certName, setCertName] = useState<string>('');
  const [certOrg, setCertOrg] = useState<string>('');
  const [certDate, setCertDate] = useState<string>('');
  const [certUrl, setCertUrl] = useState<string>('');
  const [addingCert, setAddingCert] = useState<boolean>(false);
  const [deletingCertId, setDeletingCertId] = useState<string | null>(null);

  // Form states: Add Project
  const [projTitle, setProjTitle] = useState<string>('');
  const [projDescription, setProjDescription] = useState<string>('');
  const [projTechInput, setProjTechInput] = useState<string>('');
  const [projUrl, setProjUrl] = useState<string>('');
  const [addingProj, setAddingProj] = useState<boolean>(false);
  const [deletingProjId, setDeletingProjId] = useState<string | null>(null);

  const showNotification = (msg: string) => {
    setSuccessMessage(msg);
    setTimeout(() => setSuccessMessage(null), 4000);
  };

  const showError = (msg: string) => {
    setError(msg);
    setTimeout(() => setError(null), 6000);
  };

  // Load all initial data on mount
  useEffect(() => {
    let isMounted = true;
    const loadProfileData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [
          deptData,
          skillsData,
          interestsData,
          profileData,
          studentSkillsData,
          studentInterestsData,
          certsData,
          projectsData,
        ] = await Promise.all([
          getDepartments(),
          getSkills(),
          getInterests(),
          getStudentProfile(),
          getStudentSkills(),
          getStudentInterests(),
          getStudentCertifications(),
          getStudentProjects(),
        ]);

        if (!isMounted) return;

        setDepartments(deptData);
        setAvailableSkills(skillsData);
        setAvailableInterests(interestsData);

        setProfile(profileData);
        setFullName(profileData.full_name || '');
        setDepartmentId(profileData.department_id || (deptData[0]?.id ?? ''));
        setAcademicYear(profileData.academic_year || 1);
        setBio(profileData.bio || '');
        setGithubUrl(profileData.github_url || '');
        setLinkedinUrl(profileData.linkedin_url || '');
        setPortfolioUrl(profileData.portfolio_url || '');
        setHoursPerWeek(profileData.hours_per_week || 10);

        setSkills(studentSkillsData);
        setInterests(studentInterestsData);
        setCertifications(certsData);
        setProjects(projectsData);
      } catch (err: unknown) {
        if (!isMounted) return;
        const msg = err instanceof Error ? err.message : 'Failed to load profile data';
        setError(msg);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    loadProfileData();
    return () => {
      isMounted = false;
    };
  }, []);

  // Filter available skills that student hasn't added yet
  const unselectedSkills = useMemo(() => {
    const existingIds = new Set(skills.map((s) => s.skill_id));
    return availableSkills
      .filter((s) => !existingIds.has(s.id))
      .filter((s) =>
        skillSearchQuery.trim() === ''
          ? true
          : s.name.toLowerCase().includes(skillSearchQuery.toLowerCase()) ||
            s.category.toLowerCase().includes(skillSearchQuery.toLowerCase())
      );
  }, [availableSkills, skills, skillSearchQuery]);

  // Filter available interests that student hasn't added yet
  const unselectedInterests = useMemo(() => {
    const existingIds = new Set(interests.map((i) => i.interest_id));
    return availableInterests
      .filter((i) => !existingIds.has(i.id))
      .filter((i) =>
        interestSearchQuery.trim() === ''
          ? true
          : i.name.toLowerCase().includes(interestSearchQuery.toLowerCase())
      );
  }, [availableInterests, interests, interestSearchQuery]);

  // 1. Handle Profile Update
  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fullName.trim()) {
      showError('Full name is required.');
      return;
    }

    setSavingProfile(true);
    setError(null);
    try {
      const updated = await updateStudentProfile({
        full_name: fullName.trim(),
        department_id: departmentId || null,
        academic_year: Number(academicYear),
        bio: bio.trim() || null,
        github_url: githubUrl.trim() || null,
        linkedin_url: linkedinUrl.trim() || null,
        portfolio_url: portfolioUrl.trim() || null,
        hours_per_week: Number(hoursPerWeek),
      });
      setProfile(updated);
      showNotification('Profile updated successfully!');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to update profile';
      showError(msg);
    } finally {
      setSavingProfile(false);
    }
  };

  // 2. Handle Add Skill
  const handleAddSkill = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSkillId) {
      showError('Please select a skill to add.');
      return;
    }
    setAddingSkill(true);
    try {
      const added = await addStudentSkill(selectedSkillId, skillProficiency);
      setSkills((prev) => [...prev, added]);
      setSelectedSkillId('');
      showNotification('Skill added successfully!');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to add skill';
      showError(msg);
    } finally {
      setAddingSkill(false);
    }
  };

  // Handle Remove Skill
  const handleRemoveSkill = async (skillId: string) => {
    setDeletingSkillId(skillId);
    try {
      await deleteStudentSkill(skillId);
      setSkills((prev) => prev.filter((s) => s.skill_id !== skillId));
      showNotification('Skill removed successfully.');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to remove skill';
      showError(msg);
    } finally {
      setDeletingSkillId(null);
    }
  };

  // 3. Handle Add Interest
  const handleAddInterest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedInterestId) {
      showError('Please select an interest domain.');
      return;
    }
    setAddingInterest(true);
    try {
      const added = await addStudentInterest(selectedInterestId);
      setInterests((prev) => [...prev, added]);
      setSelectedInterestId('');
      showNotification('Interest added successfully!');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to add interest';
      showError(msg);
    } finally {
      setAddingInterest(false);
    }
  };

  // Handle Remove Interest
  const handleRemoveInterest = async (interestId: string) => {
    setDeletingInterestId(interestId);
    try {
      await deleteStudentInterest(interestId);
      setInterests((prev) => prev.filter((i) => i.interest_id !== interestId));
      showNotification('Interest removed.');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to remove interest';
      showError(msg);
    } finally {
      setDeletingInterestId(null);
    }
  };

  // 4. Handle Add Certification
  const handleAddCertification = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!certName.trim() || !certOrg.trim() || !certDate.trim()) {
      showError('Certification name, issuing organization, and issue date are required.');
      return;
    }
    setAddingCert(true);
    try {
      const created = await addStudentCertification({
        name: certName.trim(),
        issuing_organization: certOrg.trim(),
        issue_date: certDate.trim(),
        credential_url: certUrl.trim() || null,
      });
      setCertifications((prev) => [created, ...prev]);
      setCertName('');
      setCertOrg('');
      setCertDate('');
      setCertUrl('');
      showNotification('Certification added successfully!');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to add certification';
      showError(msg);
    } finally {
      setAddingCert(false);
    }
  };

  // Handle Delete Certification
  const handleDeleteCertification = async (certId: string) => {
    setDeletingCertId(certId);
    try {
      await deleteStudentCertification(certId);
      setCertifications((prev) => prev.filter((c) => c.id !== certId));
      showNotification('Certification removed.');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to delete certification';
      showError(msg);
    } finally {
      setDeletingCertId(null);
    }
  };

  // 5. Handle Add Project
  const handleAddProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!projTitle.trim() || !projDescription.trim()) {
      showError('Project title and description are required.');
      return;
    }
    const techArray = projTechInput
      .split(',')
      .map((t) => t.trim())
      .filter((t) => t.length > 0);

    setAddingProj(true);
    try {
      const created = await addStudentProject({
        title: projTitle.trim(),
        description: projDescription.trim(),
        technologies: techArray,
        project_url: projUrl.trim() || null,
      });
      setProjects((prev) => [created, ...prev]);
      setProjTitle('');
      setProjDescription('');
      setProjTechInput('');
      setProjUrl('');
      showNotification('Project added successfully!');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to add project';
      showError(msg);
    } finally {
      setAddingProj(false);
    }
  };

  // Handle Delete Project
  const handleDeleteProject = async (projId: string) => {
    setDeletingProjId(projId);
    try {
      await deleteStudentProject(projId);
      setProjects((prev) => prev.filter((p) => p.id !== projId));
      showNotification('Project removed.');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to delete project';
      showError(msg);
    } finally {
      setDeletingProjId(null);
    }
  };

  const getProficiencyLabel = (level: number) => {
    switch (level) {
      case 1:
        return { label: 'Beginner', color: 'bg-blue-50 text-blue-700 border-blue-200' };
      case 2:
        return { label: 'Intermediate', color: 'bg-emerald-50 text-emerald-700 border-emerald-200' };
      case 3:
        return { label: 'Advanced', color: 'bg-indigo-50 text-indigo-700 border-indigo-200' };
      case 4:
        return { label: 'Expert', color: 'bg-purple-50 text-purple-700 border-purple-200' };
      default:
        return { label: `Level ${level}`, color: 'bg-slate-50 text-slate-700 border-slate-200' };
    }
  };

  if (loading) {
    return (
      <div className="py-20 px-4 max-w-4xl mx-auto text-center space-y-4">
        <Loader2 className="w-10 h-10 text-indigo-600 animate-spin mx-auto" />
        <h2 className="text-xl font-semibold text-slate-800">Loading Student Profile...</h2>
        <p className="text-sm text-slate-500">Retrieving academic profile, skills, and portfolio.</p>
      </div>
    );
  }

  return (
    <div className="py-8 px-4 sm:px-6 lg:px-8 max-w-6xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 flex items-center space-x-2">
            <User className="w-7 h-7 text-indigo-600" />
            <span>Student Profile</span>
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Manage your personal profile, technical skills, interests, and portfolio achievements.
          </p>
        </div>

        <div className="flex flex-col sm:items-end text-xs text-slate-500">
          <span className="font-semibold text-slate-800">{user?.email}</span>
          {profile?.updated_at && (
            <span className="text-[11px] text-slate-400">
              Updated {new Date(profile.updated_at).toLocaleDateString()}
            </span>
          )}
        </div>
      </div>

      {/* Notifications */}
      {successMessage && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
            <span className="text-sm font-medium">{successMessage}</span>
          </div>
          <button onClick={() => setSuccessMessage(null)} className="text-emerald-600 hover:text-emerald-800">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
            <span className="text-sm font-medium">{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-rose-600 hover:text-rose-800">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="flex overflow-x-auto space-x-2 border-b border-slate-200 pb-2">
        <button
          onClick={() => setActiveTab('profile')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-colors shrink-0 ${
            activeTab === 'profile'
              ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-200'
              : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
          }`}
        >
          <User className="w-4 h-4" />
          <span>Basic Profile</span>
        </button>

        <button
          onClick={() => setActiveTab('skills')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-colors shrink-0 ${
            activeTab === 'skills'
              ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-200'
              : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
          }`}
        >
          <Code className="w-4 h-4" />
          <span>Skills ({skills.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('interests')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-colors shrink-0 ${
            activeTab === 'interests'
              ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-200'
              : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
          }`}
        >
          <Sparkles className="w-4 h-4" />
          <span>Interests ({interests.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('certifications')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-colors shrink-0 ${
            activeTab === 'certifications'
              ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-200'
              : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
          }`}
        >
          <Award className="w-4 h-4" />
          <span>Certifications ({certifications.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('projects')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-colors shrink-0 ${
            activeTab === 'projects'
              ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-200'
              : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
          }`}
        >
          <Briefcase className="w-4 h-4" />
          <span>Projects ({projects.length})</span>
        </button>
      </div>

      {/* TAB 1: BASIC PROFILE */}
      {activeTab === 'profile' && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm">
          <div className="flex items-center space-x-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
              <GraduationCap className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900">Academic & Personal Details</h2>
              <p className="text-xs text-slate-500">Update your college academic identity and portfolio links.</p>
            </div>
          </div>

          <form onSubmit={handleProfileSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Full Name */}
              <div>
                <label htmlFor="full-name" className="block text-sm font-semibold text-slate-700 mb-1">
                  Full Name <span className="text-rose-500">*</span>
                </label>
                <input
                  id="full-name"
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g., Kirubakaran S"
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                />
              </div>

              {/* Department */}
              <div>
                <label htmlFor="department" className="block text-sm font-semibold text-slate-700 mb-1">
                  Academic Department
                </label>
                <select
                  id="department"
                  value={departmentId}
                  onChange={(e) => setDepartmentId(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm bg-white"
                >
                  <option value="">Select Department...</option>
                  {departments.map((dept) => (
                    <option key={dept.id} value={dept.id}>
                      {dept.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Academic Year */}
              <div>
                <label htmlFor="academic-year" className="block text-sm font-semibold text-slate-700 mb-1">
                  Academic Year (1 - 5)
                </label>
                <select
                  id="academic-year"
                  value={academicYear}
                  onChange={(e) => setAcademicYear(Number(e.target.value))}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm bg-white"
                >
                  <option value={1}>1st Year (Freshman)</option>
                  <option value={2}>2nd Year (Sophomore)</option>
                  <option value={3}>3rd Year (Junior)</option>
                  <option value={4}>4th Year (Senior)</option>
                  <option value={5}>5th Year (Dual Degree / Graduate)</option>
                </select>
              </div>

              {/* Available Hours Per Week */}
              <div>
                <label htmlFor="hours-per-week" className="block text-sm font-semibold text-slate-700 mb-1">
                  Available Hours / Week: <span className="text-indigo-600 font-bold">{hoursPerWeek} hrs</span>
                </label>
                <input
                  id="hours-per-week"
                  type="range"
                  min={1}
                  max={40}
                  value={hoursPerWeek}
                  onChange={(e) => setHoursPerWeek(Number(e.target.value))}
                  className="w-full accent-indigo-600 cursor-pointer mt-2"
                />
              </div>
            </div>

            {/* Bio */}
            <div>
              <label htmlFor="bio" className="block text-sm font-semibold text-slate-700 mb-1">
                Short Bio
              </label>
              <textarea
                id="bio"
                rows={3}
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                placeholder="Share your interests, aspirations, and what drives you..."
                className="w-full px-4 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
              />
            </div>

            {/* Social / Portfolio Links */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
              <div>
                <label htmlFor="github-url" className="block text-xs font-semibold text-slate-600 mb-1">
                  GitHub Profile URL
                </label>
                <input
                  id="github-url"
                  type="url"
                  value={githubUrl}
                  onChange={(e) => setGithubUrl(e.target.value)}
                  placeholder="https://github.com/..."
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-xs"
                />
              </div>

              <div>
                <label htmlFor="linkedin-url" className="block text-xs font-semibold text-slate-600 mb-1">
                  LinkedIn URL
                </label>
                <input
                  id="linkedin-url"
                  type="url"
                  value={linkedinUrl}
                  onChange={(e) => setLinkedinUrl(e.target.value)}
                  placeholder="https://linkedin.com/in/..."
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-xs"
                />
              </div>

              <div>
                <label htmlFor="portfolio-url" className="block text-xs font-semibold text-slate-600 mb-1">
                  Portfolio Website URL
                </label>
                <input
                  id="portfolio-url"
                  type="url"
                  value={portfolioUrl}
                  onChange={(e) => setPortfolioUrl(e.target.value)}
                  placeholder="https://..."
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-xs"
                />
              </div>
            </div>

            {/* Submit Button */}
            <div className="flex justify-end pt-4 border-t border-slate-100">
              <button
                type="submit"
                disabled={savingProfile}
                className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-indigo-600 text-white font-medium text-sm hover:bg-indigo-700 transition-colors disabled:opacity-50 shadow-sm"
              >
                {savingProfile ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Saving Changes...</span>
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4" />
                    <span>Save Profile</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* TAB 2: SKILLS */}
      {activeTab === 'skills' && (
        <div className="space-y-6">
          {/* Add Skill Form */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
            <h3 className="text-base font-bold text-slate-900 mb-3 flex items-center space-x-2">
              <Plus className="w-5 h-5 text-indigo-600" />
              <span>Add Technical Skill</span>
            </h3>

            <form onSubmit={handleAddSkill} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Search / Select Skill */}
                <div className="md:col-span-2 space-y-2">
                  <label htmlFor="skill-search" className="block text-xs font-semibold text-slate-700">
                    Search & Select Taxonomy Skill
                  </label>
                  <div className="relative">
                    <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                    <input
                      id="skill-search"
                      type="text"
                      placeholder="Filter skills by name or category (e.g., Python, Frontend)..."
                      value={skillSearchQuery}
                      onChange={(e) => setSkillSearchQuery(e.target.value)}
                      className="w-full pl-9 pr-4 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                  <select
                    id="skill-select"
                    value={selectedSkillId}
                    onChange={(e) => setSelectedSkillId(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-300 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="">-- Choose a skill ({unselectedSkills.length} available) --</option>
                    {unselectedSkills.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.name} ({s.category})
                      </option>
                    ))}
                  </select>
                </div>

                {/* Proficiency Rating */}
                <div>
                  <label htmlFor="proficiency-select" className="block text-xs font-semibold text-slate-700 mb-2">
                    Proficiency (1 to 4)
                  </label>
                  <select
                    id="proficiency-select"
                    value={skillProficiency}
                    onChange={(e) => setSkillProficiency(Number(e.target.value))}
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-300 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value={1}>1 - Beginner</option>
                    <option value={2}>2 - Intermediate</option>
                    <option value={3}>3 - Advanced</option>
                    <option value={4}>4 - Expert</option>
                  </select>
                  <div className="mt-3">
                    <button
                      type="submit"
                      disabled={addingSkill || !selectedSkillId}
                      className="w-full inline-flex items-center justify-center space-x-2 px-4 py-2.5 rounded-xl bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 transition-colors disabled:opacity-50"
                    >
                      {addingSkill ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                      <span>Add Skill</span>
                    </button>
                  </div>
                </div>
              </div>
            </form>
          </div>

          {/* Current Skills List */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
            <h3 className="text-base font-bold text-slate-900 mb-4 flex items-center justify-between">
              <span>My Skills ({skills.length})</span>
            </h3>

            {skills.length === 0 ? (
              <div className="py-12 text-center text-slate-500 space-y-2">
                <Code className="w-10 h-10 text-slate-300 mx-auto" />
                <p className="font-medium text-slate-700">No skills added yet</p>
                <p className="text-xs text-slate-400">Add technical skills to highlight your strengths for team formation.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                {skills.map((s) => {
                  const prof = getProficiencyLabel(s.proficiency);
                  return (
                    <div
                      key={s.id}
                      className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-white hover:border-slate-300 transition-all flex items-center justify-between group"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center space-x-2">
                          <span className="font-semibold text-sm text-slate-800">{s.skill_name || 'Skill'}</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className={`text-xs px-2 py-0.5 rounded-md font-semibold border ${prof.color}`}>
                            {prof.label}
                          </span>
                          {s.category && (
                            <span className="text-xs text-slate-400 uppercase tracking-wider">{s.category}</span>
                          )}
                        </div>
                      </div>

                      <button
                        onClick={() => handleRemoveSkill(s.skill_id)}
                        disabled={deletingSkillId === s.skill_id}
                        title="Remove skill"
                        className="p-2 text-slate-400 hover:text-rose-600 rounded-lg hover:bg-rose-50 transition-colors"
                      >
                        {deletingSkillId === s.skill_id ? (
                          <Loader2 className="w-4 h-4 animate-spin text-rose-500" />
                        ) : (
                          <Trash2 className="w-4 h-4" />
                        )}
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 3: INTERESTS */}
      {activeTab === 'interests' && (
        <div className="space-y-6">
          {/* Add Interest Form */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
            <h3 className="text-base font-bold text-slate-900 mb-3 flex items-center space-x-2">
              <Plus className="w-5 h-5 text-indigo-600" />
              <span>Add Project Domain Interest</span>
            </h3>

            <form onSubmit={handleAddInterest} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
                <div className="md:col-span-2 space-y-2">
                  <label htmlFor="interest-search" className="block text-xs font-semibold text-slate-700">
                    Search & Select Interest Domain
                  </label>
                  <div className="relative">
                    <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                    <input
                      id="interest-search"
                      type="text"
                      placeholder="Filter domains (e.g. AI, Robotics, Web)..."
                      value={interestSearchQuery}
                      onChange={(e) => setInterestSearchQuery(e.target.value)}
                      className="w-full pl-9 pr-4 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                  <select
                    id="interest-select"
                    value={selectedInterestId}
                    onChange={(e) => setSelectedInterestId(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-300 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="">-- Choose an interest ({unselectedInterests.length} available) --</option>
                    {unselectedInterests.map((i) => (
                      <option key={i.id} value={i.id}>
                        {i.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <button
                    type="submit"
                    disabled={addingInterest || !selectedInterestId}
                    className="w-full inline-flex items-center justify-center space-x-2 px-4 py-2.5 rounded-xl bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 transition-colors disabled:opacity-50"
                  >
                    {addingInterest ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                    <span>Add Interest</span>
                  </button>
                </div>
              </div>
            </form>
          </div>

          {/* Current Interests List */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
            <h3 className="text-base font-bold text-slate-900 mb-4">My Selected Interests ({interests.length})</h3>

            {interests.length === 0 ? (
              <div className="py-12 text-center text-slate-500 space-y-2">
                <Sparkles className="w-10 h-10 text-slate-300 mx-auto" />
                <p className="font-medium text-slate-700">No project interests selected yet</p>
                <p className="text-xs text-slate-400">Select research and development domains you are enthusiastic about.</p>
              </div>
            ) : (
              <div className="flex flex-wrap gap-3">
                {interests.map((item) => (
                  <div
                    key={item.id}
                    className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-indigo-50 text-indigo-900 border border-indigo-200 text-sm font-medium shadow-sm"
                  >
                    <span>{item.interest_name || 'Domain Interest'}</span>
                    <button
                      onClick={() => handleRemoveInterest(item.interest_id)}
                      disabled={deletingInterestId === item.interest_id}
                      title="Remove interest"
                      className="text-indigo-400 hover:text-rose-600 ml-1 transition-colors"
                    >
                      {deletingInterestId === item.interest_id ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin text-rose-500" />
                      ) : (
                        <X className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 4: CERTIFICATIONS */}
      {activeTab === 'certifications' && (
        <div className="space-y-6">
          {/* Add Certification Form */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
            <h3 className="text-base font-bold text-slate-900 mb-4 flex items-center space-x-2">
              <Award className="w-5 h-5 text-indigo-600" />
              <span>Add Accreditation / Certification</span>
            </h3>

            <form onSubmit={handleAddCertification} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="cert-name" className="block text-xs font-semibold text-slate-700 mb-1">
                    Certification Name <span className="text-rose-500">*</span>
                  </label>
                  <input
                    id="cert-name"
                    type="text"
                    required
                    placeholder="e.g., AWS Certified Cloud Practitioner"
                    value={certName}
                    onChange={(e) => setCertName(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label htmlFor="cert-org" className="block text-xs font-semibold text-slate-700 mb-1">
                    Issuing Organization <span className="text-rose-500">*</span>
                  </label>
                  <input
                    id="cert-org"
                    type="text"
                    required
                    placeholder="e.g., Amazon Web Services / Coursera"
                    value={certOrg}
                    onChange={(e) => setCertOrg(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label htmlFor="cert-date" className="block text-xs font-semibold text-slate-700 mb-1">
                    Issue Date <span className="text-rose-500">*</span>
                  </label>
                  <input
                    id="cert-date"
                    type="date"
                    required
                    value={certDate}
                    onChange={(e) => setCertDate(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
                  />
                </div>

                <div>
                  <label htmlFor="cert-url" className="block text-xs font-semibold text-slate-700 mb-1">
                    Credential Verification URL
                  </label>
                  <input
                    id="cert-url"
                    type="url"
                    placeholder="https://..."
                    value={certUrl}
                    onChange={(e) => setCertUrl(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <div className="flex justify-end pt-2">
                <button
                  type="submit"
                  disabled={addingCert}
                  className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-indigo-600 text-white font-medium text-sm hover:bg-indigo-700 transition-colors disabled:opacity-50"
                >
                  {addingCert ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                  <span>Save Certification</span>
                </button>
              </div>
            </form>
          </div>

          {/* Current Certifications List */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
            <h3 className="text-base font-bold text-slate-900 mb-4">My Certifications ({certifications.length})</h3>

            {certifications.length === 0 ? (
              <div className="py-12 text-center text-slate-500 space-y-2">
                <Award className="w-10 h-10 text-slate-300 mx-auto" />
                <p className="font-medium text-slate-700">No certifications added</p>
                <p className="text-xs text-slate-400">Add course completion badges and verified credentials.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {certifications.map((c) => (
                  <div
                    key={c.id}
                    className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-white transition-all flex items-center justify-between"
                  >
                    <div className="space-y-1">
                      <h4 className="font-semibold text-sm text-slate-900">{c.name}</h4>
                      <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500">
                        <span className="flex items-center space-x-1">
                          <Building className="w-3.5 h-3.5" />
                          <span>{c.issuing_organization}</span>
                        </span>
                        <span className="flex items-center space-x-1">
                          <Calendar className="w-3.5 h-3.5" />
                          <span>Issued {c.issue_date}</span>
                        </span>
                        {c.credential_url && (
                          <a
                            href={c.credential_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center space-x-1 text-indigo-600 hover:text-indigo-800 underline"
                          >
                            <span>Verify Credential</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                      </div>
                    </div>

                    <button
                      onClick={() => handleDeleteCertification(c.id)}
                      disabled={deletingCertId === c.id}
                      title="Delete certification"
                      className="p-2 text-slate-400 hover:text-rose-600 rounded-lg hover:bg-rose-50 transition-colors"
                    >
                      {deletingCertId === c.id ? (
                        <Loader2 className="w-4 h-4 animate-spin text-rose-500" />
                      ) : (
                        <Trash2 className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 5: PREVIOUS PROJECTS */}
      {activeTab === 'projects' && (
        <div className="space-y-6">
          {/* Add Project Form */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
            <h3 className="text-base font-bold text-slate-900 mb-4 flex items-center space-x-2">
              <Briefcase className="w-5 h-5 text-indigo-600" />
              <span>Add Portfolio Project</span>
            </h3>

            <form onSubmit={handleAddProject} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <label htmlFor="proj-title" className="block text-xs font-semibold text-slate-700 mb-1">
                    Project Title <span className="text-rose-500">*</span>
                  </label>
                  <input
                    id="proj-title"
                    type="text"
                    required
                    placeholder="e.g., Autonomous Drone Path Planner"
                    value={projTitle}
                    onChange={(e) => setProjTitle(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div className="md:col-span-2">
                  <label htmlFor="proj-desc" className="block text-xs font-semibold text-slate-700 mb-1">
                    Project Description <span className="text-rose-500">*</span>
                  </label>
                  <textarea
                    id="proj-desc"
                    rows={3}
                    required
                    placeholder="Summarize the problem solved, system architecture, and your key contributions..."
                    value={projDescription}
                    onChange={(e) => setProjDescription(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label htmlFor="proj-tech" className="block text-xs font-semibold text-slate-700 mb-1">
                    Technologies Used (comma separated)
                  </label>
                  <input
                    id="proj-tech"
                    type="text"
                    placeholder="Python, OpenCV, ROS2, PyTorch"
                    value={projTechInput}
                    onChange={(e) => setProjTechInput(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label htmlFor="proj-url" className="block text-xs font-semibold text-slate-700 mb-1">
                    Project Repository / Live URL
                  </label>
                  <input
                    id="proj-url"
                    type="url"
                    placeholder="https://github.com/..."
                    value={projUrl}
                    onChange={(e) => setProjUrl(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <div className="flex justify-end pt-2">
                <button
                  type="submit"
                  disabled={addingProj}
                  className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-indigo-600 text-white font-medium text-sm hover:bg-indigo-700 transition-colors disabled:opacity-50"
                >
                  {addingProj ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                  <span>Save Project</span>
                </button>
              </div>
            </form>
          </div>

          {/* Current Projects List */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
            <h3 className="text-base font-bold text-slate-900 mb-4">Portfolio Items ({projects.length})</h3>

            {projects.length === 0 ? (
              <div className="py-12 text-center text-slate-500 space-y-2">
                <Briefcase className="w-10 h-10 text-slate-300 mx-auto" />
                <p className="font-medium text-slate-700">No previous projects showcased</p>
                <p className="text-xs text-slate-400">Add past hackathon projects, academic assignments, or open-source repositories.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {projects.map((p) => (
                  <div
                    key={p.id}
                    className="p-5 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-white transition-all space-y-3"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <h4 className="font-bold text-base text-slate-900">{p.title}</h4>
                        <p className="text-sm text-slate-600 mt-1 leading-relaxed">{p.description}</p>
                      </div>

                      <button
                        onClick={() => handleDeleteProject(p.id)}
                        disabled={deletingProjId === p.id}
                        title="Delete project"
                        className="p-2 text-slate-400 hover:text-rose-600 rounded-lg hover:bg-rose-50 transition-colors shrink-0"
                      >
                        {deletingProjId === p.id ? (
                          <Loader2 className="w-4 h-4 animate-spin text-rose-500" />
                        ) : (
                          <Trash2 className="w-4 h-4" />
                        )}
                      </button>
                    </div>

                    <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-100">
                      <div className="flex flex-wrap gap-1.5">
                        {p.technologies && p.technologies.length > 0 ? (
                          p.technologies.map((tech, idx) => (
                            <span
                              key={idx}
                              className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-100"
                            >
                              {tech}
                            </span>
                          ))
                        ) : (
                          <span className="text-xs text-slate-400">No specific technologies tagged</span>
                        )}
                      </div>

                      {p.project_url && (
                        <a
                          href={p.project_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center space-x-1.5 text-xs font-semibold text-indigo-600 hover:text-indigo-800"
                        >
                          <span>View Project</span>
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
