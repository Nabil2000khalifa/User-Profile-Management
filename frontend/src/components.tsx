import { useEffect, useState } from "react";
import type { ReactNode } from "react";

type IconName =
  | "arrow-left"
  | "arrow-right"
  | "chevron-down"
  | "close"
  | "menu"
  | "plus"
  | "search"
  | "shield"
  | "users"
  | "logout"
  | "grid"
  | "check";

export function Icon({ name, size = 18 }: { name: IconName; size?: number }) {
  const paths: Record<IconName, ReactNode> = {
    "arrow-left":   <path d="m11 17-5-5 5-5M6 12h12" />,
    "arrow-right":  <path d="M13 7l5 5-5 5M18 12H6" />,
    "chevron-down": <path d="m6 9 6 6 6-6" />,
    close:          <path d="m6 6 12 12M18 6 6 18" />,
    menu:           <><path d="M4 6h16M4 12h16M4 18h16" /></>,
    plus:           <path d="M12 5v14M5 12h14" />,
    search:         <><circle cx="10.8" cy="10.8" r="6.8" /><path d="m16 16 4 4" /></>,
    shield:         <path d="M12 3 19 6v5c0 4.4-3 8-7 10-4-2-7-5.6-7-10V6l7-3Z" />,
    users:          <><path d="M16 20v-1.5a4.5 4.5 0 0 0-4.5-4.5h-3A4.5 4.5 0 0 0 4 18.5V20" /><circle cx="10" cy="7.5" r="3.5" /><path d="M17 11a3.5 3.5 0 1 0 0-7M16 14h1a4 4 0 0 1 4 4v2" /></>,
    logout:         <><path d="M10 5H5v14h5M15 8l4 4-4 4M19 12H9" /></>,
    grid:           <><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></>,
    check:          <path d="M20 6 9 17l-5-5" />,
  };
  return (
    <svg
      aria-hidden="true"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {paths[name]}
    </svg>
  );
}

export function Feedback({
  message,
  tone = "error",
}: {
  message: string;
  tone?: "error" | "success" | "info";
}) {
  const styles = {
    error:   "border-red-200 bg-red-50/80 text-red-800",
    success: "border-emerald-200 bg-emerald-50/80 text-emerald-800",
    info:    "border-blue-200 bg-blue-50/80 text-blue-800",
  };
  const icons = {
    error:   "!",
    success: "✓",
    info:    "i",
  };
  return (
    <div
      className={`flex items-start gap-3 rounded-xl border px-4 py-3 text-sm font-medium ${styles[tone]}`}
      role="alert"
    >
      <span className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full bg-current/10 text-xs font-black">
        {icons[tone]}
      </span>
      <span className="leading-5">{message}</span>
    </div>
  );
}

export function Field({
  label,
  error,
  hint,
  children,
}: {
  label: string;
  error?: string;
  hint?: string;
  children: ReactNode;
}) {
  return (
    <label className="grid gap-1.5 text-sm font-semibold text-slate-700">
      <span className="flex items-center justify-between gap-2">
        {label}
        {hint && (
          <span className="text-xs font-normal text-slate-400">{hint}</span>
        )}
      </span>
      {children}
      {error && (
        <span className="flex items-center gap-1.5 font-medium text-red-600 text-xs" role="alert">
          <span className="inline-grid h-4 w-4 place-items-center rounded-full bg-red-100 text-[10px] font-black">!</span>
          {error}
        </span>
      )}
    </label>
  );
}

export function TextInput(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className={`control ${props.className ?? ""}`} />;
}

export function SelectInput(
  props: React.SelectHTMLAttributes<HTMLSelectElement>,
) {
  return <select {...props} className={`control ${props.className ?? ""}`} />;
}

export function Button({
  children,
  variant = "primary",
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "quiet" | "danger";
}) {
  const styles = {
    primary:
      "bg-blue-700 text-white shadow-sm shadow-blue-900/10 hover:bg-blue-800 active:bg-blue-900 focus:ring-blue-200",
    secondary:
      "border border-slate-200 bg-white text-slate-700 shadow-sm hover:border-slate-300 hover:bg-slate-50 active:bg-slate-100 focus:ring-slate-200",
    quiet:
      "text-slate-600 hover:bg-slate-100 active:bg-slate-200 focus:ring-slate-200",
    danger:
      "border border-red-200 bg-red-50 text-red-700 hover:bg-red-100 active:bg-red-200 focus:ring-red-200",
  };
  return (
    <button
      {...props}
      className={`inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-bold transition-all focus:outline-none focus:ring-4 disabled:cursor-not-allowed disabled:opacity-50 ${styles[variant]} ${props.className ?? ""}`}
    >
      {children}
    </button>
  );
}

export function Spinner({ label = "Loading" }: { label?: string }) {
  return (
    <span
      aria-label={label}
      className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent"
    />
  );
}

export function AppShell({
  email,
  onLogout,
  children,
}: {
  email: string;
  onLogout: () => void;
  children: ReactNode;
}) {
  const [menuOpen, setMenuOpen] = useState(false);
  const initials = email.slice(0, 2).toUpperCase();

  return (
    <div className="min-h-screen bg-[#f8fafd] text-slate-900">
      {/* ── Sidebar (desktop) ─────────────────────────────────────────── */}
      <aside className="fixed inset-y-0 left-0 hidden w-64 flex-col border-r border-white/[0.06] bg-[#0b1730] lg:flex">
        {/* Logo */}
        <div className="flex h-[68px] items-center gap-3 border-b border-white/[0.07] px-6">
          <span className="brand-mark">P</span>
          <span className="text-[1.05rem] font-black tracking-tight text-white">
            Profile<span className="text-blue-400">Desk</span>
          </span>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto px-4 py-5">
          <p className="mb-3 px-2 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-600">
            Navigation
          </p>
          <div className="space-y-0.5">
            <a
              href="/dashboard"
              className="nav-link nav-link-active"
            >
              <Icon name="users" size={17} />
              <span>Directory</span>
              <span className="ml-auto flex h-5 min-w-[20px] items-center justify-center rounded-full bg-blue-500/20 px-1.5 text-[10px] font-black text-blue-300">
                ●
              </span>
            </a>

          </div>
        </nav>

        {/* Admin info footer */}
        <div className="border-t border-white/[0.07] px-4 py-4">
          <div className="flex items-center gap-3 rounded-xl bg-white/[0.05] px-3 py-2.5">
            <span className="avatar avatar-md avatar-dark flex-shrink-0" style={{ borderRadius: "50%" }}>
              {initials}
            </span>
            <div className="min-w-0">
              <p className="truncate text-xs font-bold text-white">{email}</p>
              <p className="text-[10px] text-slate-500">Administrator</p>
            </div>
            <button
              onClick={onLogout}
              title="Sign out"
              className="ml-auto flex-shrink-0 rounded-lg p-1.5 text-slate-500 transition hover:bg-white/10 hover:text-white"
            >
              <Icon name="logout" size={15} />
            </button>
          </div>
        </div>
      </aside>

      {/* ── Main content wrapper ──────────────────────────────────────── */}
      <div className="lg:pl-64">
        {/* Top header */}
        <header className="sticky top-0 z-20 border-b border-slate-200/80 bg-white/95 backdrop-blur-sm">
          <div className="flex h-[68px] items-center justify-between px-4 sm:px-7">
            {/* Mobile logo */}
            <a
              href="/dashboard"
              className="flex items-center gap-2.5 lg:hidden"
              onClick={() => setMenuOpen(false)}
            >
              <span className="brand-mark brand-mark-small">P</span>
              <span className="text-[1rem] font-black tracking-tight text-slate-900">
                Profile<span className="text-blue-700">Desk</span>
              </span>
            </a>

            {/* Desktop breadcrumb */}
            <div className="hidden lg:flex items-center gap-2 text-sm">
              <span className="font-semibold text-slate-400">Admin</span>
              <span className="text-slate-300">/</span>
              <span className="font-bold text-slate-800">Profile directory</span>
            </div>

            {/* Right actions */}
            <div className="flex items-center gap-3">
              <div className="hidden sm:flex items-center gap-2.5">
                <div className="text-right">
                  <p className="max-w-[180px] truncate text-sm font-bold text-slate-800">
                    {email}
                  </p>
                  <p className="text-[11px] text-slate-400">Administrator</p>
                </div>
                <span
                  className="avatar avatar-md flex-shrink-0 ring-4 ring-blue-50"
                  style={{ background: "#dbeafe", color: "#1d4ed8", borderRadius: "50%" }}
                >
                  {initials}
                </span>
              </div>
              <Button
                variant="secondary"
                className="hidden sm:inline-flex"
                onClick={onLogout}
              >
                <Icon name="logout" size={15} />
                Sign out
              </Button>
              <button
                className="rounded-xl p-2 text-slate-500 transition hover:bg-slate-100 lg:hidden"
                onClick={() => setMenuOpen(!menuOpen)}
                aria-label="Toggle navigation"
                aria-expanded={menuOpen}
              >
                <Icon name={menuOpen ? "close" : "menu"} />
              </button>
            </div>
          </div>

          {/* Mobile dropdown */}
          {menuOpen && (
            <div className="animate-fadeIn border-t border-slate-200 bg-white px-4 py-3 lg:hidden">
              <Button
                variant="secondary"
                className="w-full"
                onClick={onLogout}
              >
                <Icon name="logout" size={15} />
                Sign out
              </Button>
            </div>
          )}
        </header>

        {/* Page content */}
        <main className="mx-auto max-w-[1380px] px-4 py-7 sm:px-7 sm:py-9">
          {children}
        </main>
      </div>
    </div>
  );
}

export function useDebouncedValue<T>(value: T, delay = 300) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(value), delay);
    return () => window.clearTimeout(timer);
  }, [delay, value]);
  return debounced;
}
