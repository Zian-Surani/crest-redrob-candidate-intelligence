import { Link, useLocation } from "react-router-dom";
import {
  Home,
  LayoutDashboard,
  Briefcase,
  Users,
  Settings,
  LogOut,
  TrendingUp,
  ShieldAlert,
  Info,
} from "lucide-react";
import clsx from "clsx";

export default function Sidebar() {
  const location = useLocation();

  const navItems = [
    { icon: Home, label: "Overview", path: "/dashboard" },
    { icon: Users, label: "Candidates", path: "/dashboard/candidates" },
    { icon: Briefcase, label: "Jobs", path: "/dashboard/jobs" },
    { icon: LayoutDashboard, label: "Pipeline", path: "/dashboard/pipeline" },
    { icon: TrendingUp, label: "Analytics", path: "/dashboard/analytics" },
    {
      icon: ShieldAlert,
      label: "Flagged Profiles",
      path: "/dashboard/flagged",
    },
  ];

  return (
    <aside className="fixed left-6 top-6 bottom-6 w-[280px] bg-white border border-slate-200/60 rounded-premium shadow-premium flex flex-col z-50 overflow-hidden">
      <div className="h-20 flex items-center px-8 border-b border-slate-100">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-primary rounded-xl flex items-center justify-center shadow-soft">
            <span className="text-white font-bold tracking-tighter text-xl">
              C
            </span>
          </div>
          <span className="font-headline font-bold text-xl tracking-tight text-slate-900">
            CREST
          </span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto py-6 px-4 flex flex-col space-y-1">
        <p className="px-4 text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-3">
          Intelligence
        </p>

        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          const Icon = item.icon;

          return (
            <Link
              key={item.path}
              to={item.path}
              className={clsx(
                "flex items-center space-x-3 px-4 py-3 rounded-2xl transition-all duration-300 group",
                isActive
                  ? "bg-slate-50 text-slate-900 font-medium shadow-sm border border-slate-100"
                  : "text-slate-500 hover:bg-slate-50 hover:text-slate-900 border border-transparent",
              )}
            >
              <Icon
                size={18}
                strokeWidth={isActive ? 2.5 : 2}
                className={clsx(
                  "transition-colors duration-300",
                  isActive
                    ? "text-primary"
                    : "text-slate-400 group-hover:text-primary",
                )}
              />
              <span className="text-[13px]">{item.label}</span>

              {isActive && (
                <div className="ml-auto w-1.5 h-1.5 rounded-full bg-primary" />
              )}
            </Link>
          );
        })}
      </div>

      <div className="p-4 border-t border-slate-100 space-y-1">
        <Link
          to="/dashboard/settings"
          className={clsx(
            "flex items-center space-x-3 px-4 py-3 rounded-2xl transition-all duration-300",
            location.pathname === "/dashboard/settings"
              ? "bg-slate-50 text-slate-900 font-medium shadow-sm border border-slate-100"
              : "text-slate-500 hover:bg-slate-50 hover:text-slate-900",
          )}
        >
          <Settings
            size={18}
            strokeWidth={location.pathname === "/dashboard/settings" ? 2.5 : 2}
            className={clsx(
              location.pathname === "/dashboard/settings"
                ? "text-primary"
                : "text-slate-400",
            )}
          />
          <span className="text-[13px]">Settings</span>
        </Link>
        <Link
          to="/dashboard/about"
          className={clsx(
            "flex items-center space-x-3 px-4 py-3 rounded-2xl transition-all duration-300",
            location.pathname === "/dashboard/about"
              ? "bg-slate-50 text-slate-900 font-medium shadow-sm border border-slate-100"
              : "text-slate-500 hover:bg-slate-50 hover:text-slate-900",
          )}
        >
          <Info
            size={18}
            className={
              location.pathname === "/dashboard/about"
                ? "text-primary"
                : "text-slate-400"
            }
          />
          <span className="text-[13px]">About CREST</span>
        </Link>
        <Link
          to="/"
          className="w-full flex items-center space-x-3 px-4 py-3 rounded-2xl text-slate-500 hover:bg-red-50 hover:text-red-600 transition-all duration-300 group"
        >
          <LogOut
            size={18}
            strokeWidth={2}
            className="text-slate-400 group-hover:text-red-500 transition-colors"
          />
          <span className="text-[13px]">Sign Out</span>
        </Link>
      </div>
    </aside>
  );
}
