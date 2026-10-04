import React from 'react';
import { SkillGapResponse, SkillGapItem } from '../types';
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Target,
  Sparkles,
  Loader2,
  AlertCircle,
} from 'lucide-react';

interface SkillGapViewProps {
  data: SkillGapResponse | null;
  loading?: boolean;
  error?: string | null;
  isDemo?: boolean;
  title?: string;
}

export const SkillGapView: React.FC<SkillGapViewProps> = ({
  data,
  loading = false,
  error = null,
  isDemo = false,
  title = 'Skill Gap Analysis',
}) => {
  if (loading) {
    return (
      <div className="p-8 text-center bg-slate-50 border border-slate-200 rounded-2xl space-y-3">
        <Loader2 className="w-6 h-6 text-indigo-600 animate-spin mx-auto" />
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
          Calculating skill alignment & proficiency gaps...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div
        role="alert"
        className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 flex items-start space-x-3 text-sm"
      >
        <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="font-semibold">Unable to load skill gap analysis</p>
          <p className="text-xs text-rose-700">{error}</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const { summary, skills } = data;
  const coveragePercent = Math.round(summary.skill_coverage_ratio * 100);

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs space-y-5">
      {/* Header & Badges */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <Target className="w-4 h-4 text-indigo-600" />
            <h3 className="text-base font-bold text-slate-900">{title}</h3>
            {isDemo && (
              <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-amber-100 text-amber-800 border border-amber-200 flex items-center space-x-1">
                <Sparkles className="w-2.5 h-2.5 mr-1" />
                Demo Data
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500">
            {summary.overall_gap_summary}
          </p>
        </div>

        {/* Coverage Percentage Badge */}
        <div className="shrink-0 flex items-center space-x-2">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Coverage:</span>
          <span
            className={`px-3 py-1 rounded-full text-xs font-extrabold border ${
              coveragePercent >= 75
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                : coveragePercent >= 40
                ? 'bg-amber-50 text-amber-700 border-amber-200'
                : 'bg-rose-50 text-rose-700 border-rose-200'
            }`}
          >
            {coveragePercent}%
          </span>
        </div>
      </div>

      {/* Summary KPI Badges */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-2.5">
          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">Required</span>
          <span className="text-lg font-black text-slate-800">{summary.total_required_skills}</span>
        </div>
        <div className="bg-emerald-50/70 border border-emerald-200 rounded-xl p-2.5">
          <span className="text-[11px] font-bold text-emerald-700 uppercase tracking-wider block">Matched</span>
          <span className="text-lg font-black text-emerald-800">{summary.matched_count}</span>
        </div>
        <div className="bg-amber-50/70 border border-amber-200 rounded-xl p-2.5">
          <span className="text-[11px] font-bold text-amber-700 uppercase tracking-wider block">Partial Gap</span>
          <span className="text-lg font-black text-amber-800">{summary.partial_count}</span>
        </div>
        <div className="bg-rose-50/70 border border-rose-200 rounded-xl p-2.5">
          <span className="text-[11px] font-bold text-rose-700 uppercase tracking-wider block">Missing</span>
          <span className="text-lg font-black text-rose-800">{summary.missing_count}</span>
        </div>
      </div>

      {/* Detailed Skill Evaluation Items */}
      {skills.length === 0 ? (
        <div className="p-6 text-center text-slate-500 text-xs italic bg-slate-50 rounded-xl">
          This project specifies no required skills.
        </div>
      ) : (
        <div className="space-y-2.5">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block">
            Skill Breakdown
          </span>
          <div className="space-y-2">
            {skills.map((item: SkillGapItem) => {
              if (item.status === 'matched') {
                return (
                  <div
                    key={item.skill_id}
                    className="flex flex-col sm:flex-row sm:items-center justify-between p-3 rounded-xl bg-emerald-50/50 border border-emerald-200 gap-2"
                  >
                    <div className="flex items-center space-x-2.5">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                      <div>
                        <span className="text-sm font-bold text-slate-900">{item.skill_name}</span>
                        {item.category && (
                          <span className="text-[10px] text-slate-500 ml-2 font-medium">({item.category})</span>
                        )}
                        <div className="text-xs text-slate-600 mt-0.5 space-x-2">
                          <span>Required: <strong className="text-slate-800">Level {item.required_proficiency}</strong></span>
                          <span>•</span>
                          <span>Your level: <strong className="text-slate-800">Level {item.student_proficiency}</strong></span>
                        </div>
                      </div>
                    </div>
                    <span className="self-start sm:self-center px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                      Matched
                    </span>
                  </div>
                );
              }

              if (item.status === 'partial') {
                return (
                  <div
                    key={item.skill_id}
                    className="flex flex-col sm:flex-row sm:items-center justify-between p-3 rounded-xl bg-amber-50/50 border border-amber-200 gap-2"
                  >
                    <div className="flex items-center space-x-2.5">
                      <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                      <div>
                        <span className="text-sm font-bold text-slate-900">{item.skill_name}</span>
                        {item.category && (
                          <span className="text-[10px] text-slate-500 ml-2 font-medium">({item.category})</span>
                        )}
                        <div className="text-xs text-slate-600 mt-0.5 space-x-2">
                          <span>Required: <strong className="text-slate-800">Level {item.required_proficiency}</strong></span>
                          <span>•</span>
                          <span>Your level: <strong className="text-slate-800">Level {item.student_proficiency}</strong></span>
                          {item.proficiency_gap !== null && item.proficiency_gap !== undefined && (
                            <>
                              <span>•</span>
                              <span className="text-amber-800 font-semibold">
                                Gap: {item.proficiency_gap} {item.proficiency_gap === 1 ? 'level' : 'levels'}
                              </span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                    <span className="self-start sm:self-center px-2 py-0.5 rounded text-[11px] font-bold bg-amber-100 text-amber-800 border border-amber-200">
                      Proficiency Gap ({item.proficiency_gap})
                    </span>
                  </div>
                );
              }

              // Missing status
              return (
                <div
                  key={item.skill_id}
                  className="flex flex-col sm:flex-row sm:items-center justify-between p-3 rounded-xl bg-rose-50/40 border border-rose-200 gap-2"
                >
                  <div className="flex items-center space-x-2.5">
                    <XCircle className="w-4 h-4 text-rose-500 shrink-0" />
                    <div>
                      <span className="text-sm font-bold text-slate-900">{item.skill_name}</span>
                      {item.category && (
                        <span className="text-[10px] text-slate-500 ml-2 font-medium">({item.category})</span>
                      )}
                      <div className="text-xs text-slate-600 mt-0.5 space-x-2">
                        <span>Required: <strong className="text-slate-800">Level {item.required_proficiency}</strong></span>
                        <span>•</span>
                        <span className="text-rose-600 italic">Your level: Not available</span>
                      </div>
                    </div>
                  </div>
                  <span className="self-start sm:self-center px-2 py-0.5 rounded text-[11px] font-bold bg-rose-100 text-rose-800 border border-rose-200">
                    Missing
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
