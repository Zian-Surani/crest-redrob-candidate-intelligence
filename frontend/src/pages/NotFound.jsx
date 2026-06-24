import { motion } from "framer-motion";
import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 font-body px-6">
      <div className="max-w-md w-full text-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4 }}
          className="mb-8"
        >
          <div className="w-24 h-24 bg-primary/10 rounded-3xl mx-auto flex items-center justify-center mb-6">
            <span className="material-symbols-outlined text-5xl text-primary">
              search_off
            </span>
          </div>
          <h1 className="text-9xl font-headline font-bold text-slate-900 mb-4 tracking-tighter">
            404
          </h1>
          <h2 className="text-2xl font-semibold text-slate-800 mb-3">
            Page not found
          </h2>
          <p className="text-slate-500 mb-8">
            The page you are looking for doesn't exist or has been moved. Let's
            get you back on track.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="flex flex-col sm:flex-row items-center justify-center space-y-3 sm:space-y-0 sm:space-x-4"
        >
          <Link
            to="/dashboard"
            className="w-full sm:w-auto px-6 py-3 bg-primary text-white rounded-xl font-medium shadow-sm hover:-translate-y-0.5 hover:shadow-md transition-all"
          >
            Go to Dashboard
          </Link>
          <button
            onClick={() => window.history.back()}
            className="w-full sm:w-auto px-6 py-3 bg-white border border-slate-200 text-slate-700 rounded-xl font-medium hover:bg-slate-50 transition-colors"
          >
            Go Back
          </button>
        </motion.div>
      </div>
    </div>
  );
}
