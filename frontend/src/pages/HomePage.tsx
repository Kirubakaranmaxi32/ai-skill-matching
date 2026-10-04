import React from 'react';
import { Link } from 'react-router-dom';
import { Sparkles, ArrowRight, ShieldCheck } from 'lucide-react';

export const HomePage: React.FC = () => {
  return (
    <div className="py-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-12">
      {/* Hero Section */}
      <section className="text-center space-y-6 pt-8 pb-4">
        <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200 shadow-sm">
          <Sparkles className="w-3.5 h-3.5" />
          <span>AI-Driven College Student Collaboration Platform</span>
        </div>

        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-slate-900 tracking-tight">
          AI Skill Matching
        </h1>

        <p className="text-xl sm:text-2xl font-medium text-indigo-600 max-w-2xl mx-auto">
          Find the right skills. Build the right team.
        </p>

        <p className="text-slate-600 max-w-3xl mx-auto text-base sm:text-lg leading-relaxed">
          AI-Driven Student Skill Gap Analysis and Project Team Recommendation System Using Deep Learning.
          Empowering university students to discover missing technical skills and voluntarily assemble complementary project teams.
        </p>

        {/* Live AI Platform Notice Box */}
        <div className="bg-indigo-50/80 border border-indigo-200 rounded-xl p-4 max-w-2xl mx-auto text-left flex items-start space-x-3">
          <ShieldCheck className="w-5 h-5 text-indigo-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-indigo-900">
            <span className="font-semibold">Deep Learning Platform Online:</span> Featuring trained PyTorch Multi-Layer Perceptron (MLP) compatibility scoring, Sentence Transformer semantic embeddings, deterministic skill-gap analysis, voluntary team invitations, and progress tracking.
          </div>
        </div>

        {/* CTA Buttons */}
        <div className="flex flex-wrap justify-center gap-4 pt-4">
          <Link
            to="/dashboard"
            className="inline-flex items-center space-x-2 bg-indigo-600 text-white font-semibold px-6 py-3 rounded-xl shadow-md shadow-indigo-200 hover:bg-indigo-700 transition-all transform hover:-translate-y-0.5"
          >
            <span>Explore Dashboard</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            to="/login"
            className="inline-flex items-center space-x-2 bg-white text-slate-700 border border-slate-300 font-semibold px-6 py-3 rounded-xl hover:bg-slate-50 transition-all"
          >
            <span>Student Login</span>
          </Link>
        </div>
      </section>

      {/* Planned AI Workflow Pipeline Cards */}
      <section className="space-y-6 pt-6 border-t border-slate-200">
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-bold text-slate-900">End-to-End Deep Learning Architecture</h2>
          <p className="text-slate-500 text-sm">Clear mathematical and architectural separation between components</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3">
            <div className="w-10 h-10 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center font-bold">
              1
            </div>
            <h3 className="font-bold text-slate-900">Sentence Transformer</h3>
            <p className="text-sm text-slate-600">
              Pretrained NLP text representation component generating 384-dimensional dense semantic project embeddings.
            </p>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold">
              2
            </div>
            <h3 className="font-bold text-slate-900">Deterministic Gap Analysis</h3>
            <p className="text-sm text-slate-600">
              Mathematical set difference (S_required \ S_team) detecting exact unfulfilled team skill requirements.
            </p>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3">
            <div className="w-10 h-10 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold">
              3
            </div>
            <h3 className="font-bold text-slate-900">PyTorch MLP Model</h3>
            <p className="text-sm text-slate-600">
              The core trainable Deep Learning model learning non-linear compatibility surfaces from 10-D fused feature tensors.
            </p>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3">
            <div className="w-10 h-10 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center font-bold">
              4
            </div>
            <h3 className="font-bold text-slate-900">Voluntary Recommendations</h3>
            <p className="text-sm text-slate-600">
              Explainable candidate ranking with transparent data-backed rationale. Teams are formed only via mutual acceptance.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
};
