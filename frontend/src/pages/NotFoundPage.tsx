import React from 'react';
import { Link } from 'react-router-dom';

export const NotFoundPage: React.FC = () => {
  return (
    <div className="py-20 text-center space-y-4">
      <h1 className="text-4xl font-extrabold text-slate-900">404</h1>
      <p className="text-slate-600">Page not found</p>
      <Link to="/" className="inline-block text-indigo-600 font-semibold hover:underline">
        Return to Home
      </Link>
    </div>
  );
};
