import { useRef } from "react";
import { motion, useScroll, useTransform } from "framer-motion";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  ShieldCheck,
  Activity,
  CheckCircle2,
  TrendingUp,
  Users,
  Brain,
  Network,
  FileText,
} from "lucide-react";
import InteractiveBackground from "../components/InteractiveBackground";

function Navbar() {
  return (
    <nav className="fixed top-0 inset-x-0 z-50 transition-all duration-300">
      <div className="mx-auto max-w-6xl px-4 py-4">
        <div className="flex items-center justify-between rounded-xl bg-white/60 backdrop-blur-xl border border-slate-200/50 px-5 py-3 shadow-sm">
          <div className="flex items-center gap-3">
            <img src="/favicon.svg" alt="CREST" className="w-10 h-10 object-contain drop-shadow-sm" />
            <span className="font-headline text-xl font-bold tracking-wider text-slate-900">
              CREST
            </span>
          </div>
          <div className="flex items-center gap-3">
            <Link
              to="/dashboard"
              className="font-headline tracking-wider rounded-lg bg-slate-900/90 backdrop-blur-md border border-slate-700/50 px-5 py-2.5 text-sm font-semibold text-white shadow-md transition-all hover:bg-slate-800 hover:shadow-lg active:scale-95"
            >
              Enter App
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}

function Hero() {
  const ref = useRef(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start start", "end start"],
  });

  const y = useTransform(scrollYProgress, [0, 1], ["0%", "20%"]);
  const opacity = useTransform(scrollYProgress, [0, 0.5], [1, 0]);

  return (
    <motion.section
      ref={ref}
      style={{ y, opacity }}
      className="relative z-10 flex min-h-[90vh] flex-col items-center justify-center px-4 pt-16"
    >
      <div className="mx-auto max-w-4xl text-center">
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="mb-6 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-3 py-1.5 text-sm font-semibold text-primary backdrop-blur-md"
        >
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-75"></span>
            <span className="relative inline-flex h-2 w-2 rounded-full bg-primary"></span>
          </span>
          Introducing CREST Copilot 2.0
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.1, ease: "easeOut" }}
          className="font-headline mb-6 text-6xl font-extrabold leading-[1.1] tracking-tight text-slate-800 md:text-8xl"
        >
          <span className="text-slate-700/80">Recruitment intelligence</span>
          <br />
          <span className="text-primary drop-shadow-sm">reimagined.</span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }}
          className="mx-auto mb-10 max-w-2xl text-lg text-slate-500 md:text-xl leading-relaxed font-medium"
        >
          CREST is the premium OS for modern talent teams. Combine AI-driven
          sourcing, predictive pipeline analytics, and automated candidate
          engagement in one beautiful platform.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.3, ease: "easeOut" }}
          className="flex flex-col items-center justify-center gap-4 sm:flex-row"
        >
          <Link
            to="/dashboard"
            className="group font-headline tracking-wider flex w-full items-center justify-center gap-2 rounded-xl bg-primary px-8 py-4 text-base font-bold text-white shadow-xl shadow-primary/20 transition-all hover:scale-105 hover:shadow-2xl hover:shadow-primary/30 sm:w-auto"
          >
            Start Intelligence Platform
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
          </Link>
          <a
            href="#story"
            className="w-full font-headline tracking-wider rounded-xl border border-slate-200/80 bg-white/60 backdrop-blur-md px-8 py-4 text-base font-bold text-slate-700 transition-all hover:bg-white sm:w-auto text-center shadow-sm hover:shadow-md"
          >
            Take a deep dive
          </a>
        </motion.div>
      </div>
    </motion.section>
  );
}

function StoryCard({
  icon: Icon,
  title,
  description,
  delay,
  reverse = false,
  visuals,
}) {
  return (
    <motion.div
      initial={{ opacity: 0, x: reverse ? 30 : -30 }}
      whileInView={{ opacity: 1, x: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ duration: 0.8, delay, ease: "easeOut" }}
      className={`flex flex-col justify-between gap-12 lg:flex-row lg:items-center ${
        reverse ? "lg:flex-row-reverse" : ""
      }`}
    >
      <div className="flex-1 space-y-5">
        <div className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-white to-slate-100 shadow-md shadow-primary/10 border border-white/60">
          <Icon className="h-7 w-7 text-primary" />
        </div>
        <h2 className="font-headline text-4xl font-bold tracking-tight text-slate-900 md:text-5xl">
          {title}
        </h2>
        <p className="text-xl leading-relaxed text-slate-500 max-w-lg font-medium">
          {description}
        </p>
      </div>
      <div className="flex-1 w-full max-w-md mx-auto lg:max-w-none">
        <div className="relative h-[360px] w-full rounded-[2.5rem] bg-white/40 backdrop-blur-md border border-white/60 overflow-hidden group shadow-2xl shadow-slate-200/50">
          <div className="absolute inset-0 bg-gradient-to-br from-white/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700"></div>
          <div className="absolute inset-0 flex items-center justify-center p-8 mix-blend-multiply">
            {visuals}
          </div>
        </div>
      </div>
    </motion.div>
  );
}

function Story() {
  return (
    <section
      id="story"
      className="relative z-10 mx-auto max-w-6xl px-6 py-24 mt-32 space-y-40"
    >
      <StoryCard
        icon={Brain}
        title="Predictive Sourcing."
        description="Our proprietary AI models analyze millions of data points to identify top candidates before they even start looking. Hire with precision and speed."
        delay={0.1}
        visuals={
          <div className="w-full h-full rounded-3xl bg-white/80 border border-white backdrop-blur-sm p-6 shadow-2xl transition-transform duration-700 group-hover:scale-[1.02] flex flex-col justify-center gap-4">
            <div className="flex items-center gap-3 border-b border-slate-100 pb-4">
              <CheckCircle2 className="h-6 w-6 text-success" />
              <span className="text-base font-bold text-slate-800">
                12M+ Profiles Analyzed
              </span>
            </div>
            <div className="flex items-center gap-3 border-b border-slate-100 pb-4">
              <ShieldCheck className="h-6 w-6 text-success" />
              <span className="text-base font-bold text-slate-800">
                Bias-Free Algorithms
              </span>
            </div>
            <div className="flex items-center gap-3">
              <FileText className="h-6 w-6 text-primary" />
              <span className="text-base font-bold text-slate-800">
                Automated Screening
              </span>
            </div>
          </div>
        }
      />
      <StoryCard
        icon={Activity}
        title="Pipeline clarity."
        description="We distill complex hiring funnels into an intuitive interface. Everything is easy to understand at a glance, allowing you to focus on the candidates, not the platform."
        delay={0.1}
        reverse={true}
        visuals={
          <div className="w-full h-full rounded-3xl bg-white/80 border border-white backdrop-blur-sm p-6 shadow-2xl transition-transform duration-700 group-hover:-rotate-2 group-hover:scale-[1.02] flex flex-col justify-end gap-3 relative overflow-hidden">
            <div className="absolute top-6 left-6">
              <TrendingUp className="h-6 w-6 text-primary mb-2" />
              <span className="text-sm font-bold text-slate-500">
                Velocity Overview
              </span>
            </div>
            <div className="flex items-end gap-3 h-40 mt-12">
              {[40, 70, 50, 90, 60, 100, 80].map((h, i) => (
                <div
                  key={i}
                  className="w-full rounded-t-md bg-gradient-to-t from-blue-100 to-primary"
                  style={{ height: `${h}%` }}
                ></div>
              ))}
            </div>
          </div>
        }
      />
      <StoryCard
        icon={Network}
        title="Global Talent Graph."
        description="Access an interconnected graph of professional relationships, skills, and career trajectories across 150+ countries. The ultimate sourcing weapon."
        delay={0.1}
        visuals={
          <div className="w-full h-full rounded-3xl bg-white/80 border border-white backdrop-blur-sm p-6 shadow-2xl transition-transform duration-700 group-hover:scale-[1.05] flex items-center justify-center relative">
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-blue-50/50 via-transparent to-transparent"></div>
            <div className="relative flex flex-col items-center justify-center gap-5">
              <div className="h-20 w-20 bg-gradient-to-tr from-accent to-primary rounded-full flex items-center justify-center shadow-xl shadow-accent/30 animate-pulse">
                <Users className="h-8 w-8 text-white" />
              </div>
              <div className="flex gap-4">
                <div className="h-12 w-12 bg-white shadow-md rounded-full border border-slate-100 flex items-center justify-center text-xs font-bold text-slate-400">
                  AI
                </div>
                <div className="h-12 w-12 bg-white shadow-md rounded-full border border-slate-100 flex items-center justify-center text-xs font-bold text-slate-400">
                  ML
                </div>
                <div className="h-12 w-12 bg-white shadow-md rounded-full border border-slate-100 flex items-center justify-center text-xs font-bold text-slate-400">
                  NLP
                </div>
              </div>
              <span className="text-sm font-bold text-slate-500 mt-3 tracking-widest uppercase">
                Predictive Network
              </span>
            </div>
          </div>
        }
      />
    </section>
  );
}

export default function LandingPage() {
  return (
    <div className="relative min-h-screen bg-slate-50/80 selection:bg-primary/20 font-body overflow-x-hidden">
      <InteractiveBackground />
      <Navbar />
      <Hero />
      <Story />

      {/* Footer */}
      <footer className="relative z-10 border-t border-slate-200/50 bg-white/40 backdrop-blur-xl py-12 mt-20">
        <div className="mx-auto max-w-6xl px-6 text-center text-sm font-medium text-slate-500">
          <p>
            © {new Date().getFullYear()} CREST Intelligence. Premium Talent OS.
          </p>
        </div>
      </footer>
    </div>
  );
}
