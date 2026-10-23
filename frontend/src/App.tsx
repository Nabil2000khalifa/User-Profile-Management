import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { legacyCreateColumnHelper, useLegacyTable } from "@tanstack/react-table/legacy";
import type { LegacyColumnDef } from "@tanstack/react-table/legacy";

import { api, ApiError } from "./api/client";
import { useAuth } from "./auth";
import {
  AppShell,
  Button,
  Feedback,
  Field,
  Icon,
  SelectInput,
  Spinner,
  TextInput,
  useDebouncedValue,
} from "./components";
import {
  loginSchema,
  profileSchema,
  type LoginValues,
  type ProfileValues,
} from "./schemas";
import type { Profile, ProfilePage } from "./types";

type Page = { name: "dashboard" } | { name: "detail"; id: number };

/* ────────────────────────────────────────────────────────────────────────── */
/*  Login Page                                                                */
/* ────────────────────────────────────────────────────────────────────────── */
function LoginPage() {
  const { login } = useAuth();
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const {
    register,
    handleSubmit,
    setError: setFieldError,
    formState: { errors },
  } = useForm<LoginValues>();

  const submit = async (values: LoginValues) => {
    const parsed = loginSchema.safeParse(values);
    if (!parsed.success) {
      parsed.error.issues.forEach((issue) =>
        setFieldError(issue.path[0] as keyof LoginValues, {
          message: issue.message,
        }),
      );
      return;
    }
    setSaving(true);
    const result = await login(values.email, values.password);
    setSaving(false);
    if (result) setError(result.message);
  };

  return (
    <div className="login-page">
      {/* Decorative orbs */}
      <div
        style={{
          position: "absolute", top: "5%", left: "5%",
          width: "400px", height: "400px", borderRadius: "50%",
          background: "rgb(37 99 235 / 0.10)", filter: "blur(80px)",
          pointerEvents: "none",
        }}
      />
      <div
        style={{
          position: "absolute", bottom: "5%", right: "5%",
          width: "280px", height: "280px", borderRadius: "50%",
          background: "rgb(99 102 241 / 0.08)", filter: "blur(80px)",
          pointerEvents: "none",
        }}
      />

      {/* Top-left brand */}
      <div className="absolute left-6 top-6 flex items-center gap-3 sm:left-10 sm:top-8" style={{ zIndex: 2 }}>
        <span className="brand-mark">P</span>
        <span className="text-lg font-black tracking-tight text-white">
          Profile<span className="text-blue-300">Desk</span>
        </span>
      </div>

      {/* Login card */}
      <div className="login-card w-full max-w-[420px] p-7 sm:p-10 animate-fadeInUp">
        {/* Header */}
        <div className="mb-8">
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 shadow-sm">
            <Icon name="shield" size={22} />
          </div>
          <p className="eyebrow mb-2">Administrator access</p>
          <h1 className="text-2xl font-black tracking-tight text-[#0b1730] sm:text-3xl">
            Welcome back
          </h1>
          <p className="mt-2 text-sm leading-6 text-slate-500">
            Sign in to your secure workspace to manage user profiles.
          </p>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-5">
            <Feedback message={error} />
          </div>
        )}

        {/* Form */}
        <form className="grid gap-5" onSubmit={handleSubmit(submit)} noValidate>
          <Field label="Admin email" error={errors.email?.message}>
            <TextInput
              type="email"
              autoComplete="username"
              placeholder="admin@example.com"
              {...register("email")}
              aria-invalid={Boolean(errors.email)}
            />
          </Field>
          <Field label="Password" error={errors.password?.message}>
            <TextInput
              type="password"
              autoComplete="current-password"
              placeholder="••••••••"
              {...register("password")}
              aria-invalid={Boolean(errors.password)}
            />
          </Field>
          <Button
            type="submit"
            disabled={saving}
            className="mt-2 w-full py-3 text-base"
          >
            {saving ? (
              <>
                <Spinner /> Signing in…
              </>
            ) : (
              <>
                <Icon name="shield" size={16} /> Sign in securely
              </>
            )}
          </Button>
        </form>

        <p className="mt-8 text-center text-xs text-slate-400">
          Private directory · Administrator access only
        </p>
      </div>
    </div>
  );
}

/* ────────────────────────────────────────────────────────────────────────── */
/*  Profile Form                                                              */
/* ────────────────────────────────────────────────────────────────────────── */
function ProfileForm({ onCreated }: { onCreated: (profile: Profile) => void }) {
  const [countries, setCountries] = useState<string[]>([]);
  const [cities, setCities] = useState<string[]>([]);
  const [loadingLocations, setLoadingLocations] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    setError: setFieldError,
    watch,
    formState: { errors },
  } = useForm<ProfileValues>();
  const country = watch("country");

  useEffect(() => {
    api
      .countries()
      .then((result) => setCountries(result.items))
      .catch(() => setError("Unable to load countries."))
      .finally(() => setLoadingLocations(false));
  }, []);

  useEffect(() => {
    setCities([]);
    setValue("city", "");
    if (!country) return;
    api
      .cities(country)
      .then((result) => setCities(result.items))
      .catch(() => setError("Unable to load cities."));
  }, [country, setValue]);

  const submit = async (values: ProfileValues) => {
    const parsed = profileSchema.safeParse(values);
    if (!parsed.success) {
      parsed.error.issues.forEach((issue) =>
        setFieldError(issue.path[0] as keyof ProfileValues, {
          message: issue.message,
        }),
      );
      return;
    }
    setSaving(true);
    setError("");
    try {
      const profile = await api.createProfile(values);
      reset();
      setCities([]);
      onCreated(profile);
    } catch (reason) {
      const apiError =
        reason instanceof ApiError
          ? reason
          : new ApiError(0, "Unable to save the profile.");
      Object.entries(apiError.fieldErrors).forEach(([field, message]) =>
        setFieldError(field as keyof ProfileValues, { message }),
      );
      setError(apiError.status === 409 ? "" : apiError.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="surface-card overflow-hidden animate-fadeInUp">
      {/* Card header */}
      <div className="flex items-center justify-between gap-4 border-b border-slate-100 bg-gradient-to-r from-slate-50 to-white px-6 py-5">
        <div>
          <p className="eyebrow">New record</p>
          <h2 className="mt-1 text-lg font-black text-slate-900">
            Create profile
          </h2>
          <p className="mt-0.5 text-sm text-slate-500">
            All fields are required.
          </p>
        </div>
        <span className="hidden rounded-xl bg-amber-50 px-3 py-1.5 text-xs font-bold text-amber-700 ring-1 ring-amber-200/60 sm:block">
          All fields required
        </span>
      </div>

      {/* Form body */}
      <div className="p-6">
        {error && (
          <div className="mb-5">
            <Feedback message={error} />
          </div>
        )}
        <form
          className="grid gap-5 sm:grid-cols-2"
          onSubmit={handleSubmit(submit)}
          noValidate
        >
          <Field label="First name" error={errors.first_name?.message}>
            <TextInput
              placeholder="John"
              {...register("first_name")}
              aria-invalid={Boolean(errors.first_name)}
            />
          </Field>
          <Field label="Last name" error={errors.last_name?.message}>
            <TextInput
              placeholder="Doe"
              {...register("last_name")}
              aria-invalid={Boolean(errors.last_name)}
            />
          </Field>
          <Field label="Date of birth" error={errors.date_of_birth?.message}>
            <TextInput
              type="date"
              min="1900-01-01"
              {...register("date_of_birth")}
              aria-invalid={Boolean(errors.date_of_birth)}
            />
          </Field>
          <Field label="Email address" error={errors.email?.message}>
            <TextInput
              type="email"
              placeholder="john@example.com"
              {...register("email")}
              aria-invalid={Boolean(errors.email)}
            />
          </Field>
          <Field label="Country" error={errors.country?.message}>
            <SelectInput
              {...register("country")}
              disabled={loadingLocations}
              aria-invalid={Boolean(errors.country)}
            >
              <option value="">Select country</option>
              {countries.map((item) => (
                <option key={item}>{item}</option>
              ))}
            </SelectInput>
          </Field>
          <Field label="City" error={errors.city?.message}>
            <SelectInput
              {...register("city")}
              disabled={!country || cities.length === 0}
              aria-invalid={Boolean(errors.city)}
            >
              <option value="">
                {!country
                  ? "Select a country first"
                  : cities.length === 0
                    ? "Loading cities…"
                    : "Select city"}
              </option>
              {cities.map((item) => (
                <option key={item}>{item}</option>
              ))}
            </SelectInput>
          </Field>
          <div className="flex items-center justify-between gap-3 sm:col-span-2">
            <p className="text-xs text-slate-400">
              <Icon name="shield" size={13} />
              {" "}Profile data is stored securely.
            </p>
            <Button
              type="submit"
              disabled={saving || loadingLocations}
              className="px-6"
            >
              {saving ? (
                <>
                  <Spinner /> Saving…
                </>
              ) : (
                <>
                  <Icon name="plus" size={15} /> Save profile
                </>
              )}
            </Button>
          </div>
        </form>
      </div>
    </section>
  );
}

/* ────────────────────────────────────────────────────────────────────────── */
/*  Stat Card                                                                 */
/* ────────────────────────────────────────────────────────────────────────── */
function SummaryCard({
  label,
  value,
  detail,
  variant = "blue",
  iconName,
}: {
  label: string;
  value: string | number;
  detail: string;
  variant?: "blue" | "indigo" | "violet";
  iconName: "users" | "grid" | "arrow-right";
}) {
  return (
    <div className={`stat-card stat-card-${variant} animate-fadeInUp`}>
      <div className="relative z-10 flex items-start justify-between">
        <p className="eyebrow-white">{label}</p>
        <span className="grid h-9 w-9 place-items-center rounded-xl bg-white/10">
          <Icon name={iconName} size={18} />
        </span>
      </div>
      <p className="relative z-10 mt-4 text-3xl font-black tracking-tight">
        {value}
      </p>
      <p className="relative z-10 mt-1 text-sm text-white/60">{detail}</p>
    </div>
  );
}

/* ────────────────────────────────────────────────────────────────────────── */
/*  Dashboard                                                                 */
/* ────────────────────────────────────────────────────────────────────────── */
const columnHelper = legacyCreateColumnHelper<Profile>();
const columns = [
  columnHelper.accessor("first_name", { header: "First name" }),
  columnHelper.accessor("last_name", { header: "Last name" }),
  columnHelper.accessor("email", { header: "Email" }),
  columnHelper.accessor("country", { header: "Country" }),
  columnHelper.accessor("city", { header: "City" }),
];

function Dashboard({ onNavigate }: { onNavigate: (page: Page) => void }) {
  const [data, setData] = useState<ProfilePage | null>(null);
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");
  const debouncedQuery = useDebouncedValue(query);

  const load = () => {
    setError("");
    api
      .profiles(debouncedQuery, page)
      .then(setData)
      .catch(() =>
        setError("Unable to load profiles. Please retry."),
      );
  };

  useEffect(() => { load(); }, [debouncedQuery, page]);
  useEffect(() => { setPage(1); }, [debouncedQuery]);

  const table = useLegacyTable<Profile>({
    data: data?.items ?? [],
    columns: columns as LegacyColumnDef<Profile>[],
  });
  const totalPages = data?.total_pages ?? 0;

  return (
    <div className="grid gap-7">
      {/* Page header */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end animate-fadeInUp">
        <div>
          <p className="eyebrow">Directory overview</p>
          <h1 className="mt-2 text-2xl font-black tracking-tight text-[#0b1730] sm:text-3xl">
            User profiles
          </h1>
          <p className="mt-1.5 text-sm leading-6 text-slate-500">
            Search, review, and securely manage your directory.
          </p>
        </div>
        <Button
          onClick={() => {
            setShowForm(!showForm);
            setSuccessMsg("");
          }}
          variant={showForm ? "secondary" : "primary"}
          className="shrink-0"
        >
          {showForm ? (
            <>
              <Icon name="close" size={15} /> Close form
            </>
          ) : (
            <>
              <Icon name="plus" size={15} /> Create profile
            </>
          )}
        </Button>
      </div>

      {/* Stat cards */}
      <div className="grid gap-4 sm:grid-cols-3 stagger-children">
        <SummaryCard
          label="Total profiles"
          value={data?.total ?? "—"}
          detail="In your directory"
          variant="blue"
          iconName="users"
        />
        <SummaryCard
          label="Records shown"
          value={data ? `${data.items.length}` : "—"}
          detail="On current page"
          variant="indigo"
          iconName="grid"
        />
        <SummaryCard
          label="Pagination"
          value={data ? `${data.page} / ${Math.max(data.total_pages, 1)}` : "—"}
          detail="Server-side paging"
          variant="violet"
          iconName="arrow-right"
        />
      </div>

      {/* Success message */}
      {successMsg && (
        <div className="animate-fadeIn">
          <Feedback message={successMsg} tone="success" />
        </div>
      )}

      {/* Profile form */}
      {showForm && (
        <ProfileForm
          onCreated={(profile) => {
            setShowForm(false);
            setSuccessMsg(
              `Profile for ${profile.first_name} ${profile.last_name} was created successfully.`,
            );
            setData((current) =>
              current
                ? {
                    ...current,
                    items: [profile, ...current.items],
                    total: current.total + 1,
                  }
                : current,
            );
            setTimeout(() => setSuccessMsg(""), 5000);
          }}
        />
      )}

      {/* Directory table card */}
      <section className="surface-card overflow-hidden animate-fadeInUp">
        {/* Table header */}
        <div className="flex flex-col gap-4 border-b border-slate-100 px-5 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <div>
            <h2 className="font-black text-slate-900">Directory records</h2>
            <p className="mt-0.5 text-sm text-slate-500">
              Search by first or last name.
            </p>
          </div>
          {/* Search */}
          <div className="relative w-full sm:w-72">
            <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
              <Icon name="search" size={16} />
            </span>
            <label className="sr-only" htmlFor="search">
              Search profiles
            </label>
            <TextInput
              id="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search profiles…"
              style={{ paddingLeft: "2.25rem" }}
            />
          </div>
        </div>

        {/* Table body states */}
        {error ? (
          <div className="p-8">
            <Feedback message={error} />
            <Button className="mt-4" variant="secondary" onClick={load}>
              Retry loading
            </Button>
          </div>
        ) : !data ? (
          <div className="grid place-items-center gap-3 py-20 text-slate-400">
            <Spinner label="Loading profiles" />
            <span className="text-sm">Loading directory…</span>
          </div>
        ) : data.items.length === 0 ? (
          <div className="py-20 text-center">
            <div className="mx-auto grid h-16 w-16 place-items-center rounded-2xl bg-blue-50 text-blue-600">
              <Icon name="search" size={24} />
            </div>
            <p className="mt-4 font-black text-slate-800">No profiles found</p>
            <p className="mt-1 text-sm text-slate-500">
              {query
                ? "Try a different search term."
                : "Create the first profile to get started."}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table min-w-[700px]">
              <thead>
                <tr>
                  <th style={{ width: "2.5rem" }} />
                  {table.getHeaderGroups()[0].headers.map((header) => (
                    <th key={header.id}>
                      {header.column.columnDef.header as string}
                    </th>
                  ))}
                  <th />
                </tr>
              </thead>
              <tbody>
                {table.getRowModel().rows.map((row) => {
                  const firstName = row.original.first_name;
                  const lastName = row.original.last_name;
                  const initials = `${firstName[0] ?? ""}${lastName[0] ?? ""}`.toUpperCase();
                  return (
                    <tr key={row.id}>
                      {/* Avatar cell */}
                      <td className="pl-5 pr-0">
                        <span className="profile-initials">{initials}</span>
                      </td>
                      {row.getVisibleCells().map((cell) => (
                        <td key={cell.id}>
                          {cell.column.id === "email" ? (
                            <span className="text-slate-400 text-[13px]">
                              {cell.getValue() as string}
                            </span>
                          ) : cell.column.id === "country" ? (
                            <span className="badge badge-blue">
                              {cell.getValue() as string}
                            </span>
                          ) : (
                            <span className="font-medium text-slate-800">
                              {cell.getValue() as string}
                            </span>
                          )}
                        </td>
                      ))}
                      <td className="pr-4 text-right">
                        <Button
                          variant="quiet"
                          onClick={() =>
                            onNavigate({ name: "detail", id: row.original.id })
                          }
                          className="text-xs"
                        >
                          View{" "}
                          <Icon name="arrow-right" size={13} />
                        </Button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination footer */}
        {data && totalPages > 0 && (
          <div className="flex flex-col gap-3 border-t border-slate-100 px-5 py-4 text-sm sm:flex-row sm:items-center sm:justify-between">
            <span className="text-slate-500">
              Page{" "}
              <strong className="text-slate-800">{data.page}</strong> of{" "}
              <strong className="text-slate-800">{totalPages}</strong>
              <span className="ml-3 text-slate-400">
                ({data.total} total record{data.total !== 1 ? "s" : ""})
              </span>
            </span>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
                className="text-xs"
              >
                <Icon name="arrow-left" size={13} /> Previous
              </Button>
              <Button
                variant="secondary"
                disabled={page >= totalPages}
                onClick={() => setPage(page + 1)}
                className="text-xs"
              >
                Next <Icon name="arrow-right" size={13} />
              </Button>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}

/* ────────────────────────────────────────────────────────────────────────── */
/*  Detail Page                                                               */
/* ────────────────────────────────────────────────────────────────────────── */
function Detail({ id, onBack }: { id: number; onBack: () => void }) {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .profile(id)
      .then(setProfile)
      .catch(() => setError("Unable to load this profile."));
  }, [id]);

  if (error) {
    return (
      <div className="grid gap-6 animate-fadeIn">
        <Button variant="quiet" onClick={onBack} className="w-fit">
          <Icon name="arrow-left" size={15} /> Back to profiles
        </Button>
        <Feedback message={error} />
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="grid place-items-center py-24">
        <Spinner label="Loading profile" />
        <p className="mt-3 text-sm text-slate-400">Loading profile…</p>
      </div>
    );
  }

  const initials = `${profile.first_name[0] ?? ""}${profile.last_name[0] ?? ""}`.toUpperCase();

  const fields: [string, string][] = [
    ["Email address", profile.email],
    ["Date of birth", profile.date_of_birth],
    ["Country", profile.country],
    ["City", profile.city],
    ["Created", profile.created_at ? new Date(profile.created_at).toLocaleDateString() : "—"],
    ["Last updated", profile.updated_at ? new Date(profile.updated_at).toLocaleDateString() : "—"],
  ];

  return (
    <div className="grid gap-6 animate-fadeInUp">
      <Button variant="quiet" onClick={onBack} className="w-fit">
        <Icon name="arrow-left" size={15} /> Back to profiles
      </Button>

      <section className="surface-card overflow-hidden">
        {/* Profile header */}
        <div className="border-b border-slate-100 bg-gradient-to-br from-[#0b1730] to-[#1e3a8a] p-6 sm:p-8">
          <p className="eyebrow-white">Profile details</p>
          <div className="mt-5 flex items-center gap-4">
            <span
              className="avatar avatar-lg avatar-dark text-2xl"
              style={{
                background: "rgba(255,255,255,0.12)",
                backdropFilter: "blur(12px)",
                border: "1.5px solid rgba(255,255,255,0.2)",
              }}
            >
              {initials}
            </span>
            <div>
              <h1 className="text-2xl font-black text-white sm:text-3xl">
                {profile.first_name} {profile.last_name}
              </h1>
              <p className="mt-1 flex items-center gap-2 text-sm text-white/50">
                <span className="badge badge-blue text-[10px]">
                  {profile.country}
                </span>
                Directory profile · ID #{profile.id}
              </p>
            </div>
          </div>
        </div>

        {/* Fields grid */}
        <div className="p-6 sm:p-8">
          <h2 className="mb-5 text-xs font-bold uppercase tracking-widest text-slate-400">
            Profile information
          </h2>
          <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {fields.map(([label, value]) => (
              <div className="detail-field" key={label}>
                <dt className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  {label}
                </dt>
                <dd className="mt-2 text-sm font-semibold text-slate-900 break-all">
                  {value}
                </dd>
              </div>
            ))}
          </dl>
        </div>
      </section>
    </div>
  );
}

/* ────────────────────────────────────────────────────────────────────────── */
/*  App root                                                                  */
/* ────────────────────────────────────────────────────────────────────────── */
export default function App() {
  const { admin, loading, error: sessionError, logout } = useAuth();
  const [page, setPage] = useState<Page>(() =>
    parsePage(window.location.pathname),
  );

  const navigate = (nextPage: Page) => {
    const path =
      nextPage.name === "dashboard"
        ? "/dashboard"
        : `/profiles/${nextPage.id}`;
    window.history.pushState({}, "", path);
    setPage(nextPage);
  };

  useEffect(() => {
    const handlePopState = () => setPage(parsePage(window.location.pathname));
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  useEffect(() => {
    if (!admin && !loading && window.location.pathname !== "/login") {
      window.history.replaceState({}, "", "/login");
      setPage({ name: "dashboard" });
    } else if (admin && window.location.pathname === "/login") {
      window.history.replaceState({}, "", "/dashboard");
      setPage({ name: "dashboard" });
    }
  }, [admin, loading]);

  if (loading) {
    return (
      <div className="grid min-h-screen place-items-center bg-[#f8fafd]">
        <div className="flex flex-col items-center gap-4">
          <span className="brand-mark">P</span>
          <Spinner label="Checking session" />
          <p className="text-sm text-slate-400">Verifying session…</p>
        </div>
      </div>
    );
  }

  if (!admin) return <LoginPage />;

  if (sessionError) {
    return (
      <div className="p-8">
        <Feedback message={sessionError} />
      </div>
    );
  }

  return (
    <AppShell email={admin.email} onLogout={() => void logout()}>
      {page.name === "detail" ? (
        <Detail
          id={page.id}
          onBack={() => navigate({ name: "dashboard" })}
        />
      ) : (
        <Dashboard onNavigate={navigate} />
      )}
    </AppShell>
  );
}

function parsePage(pathname: string): Page {
  const match = pathname.match(/^\/profiles\/(\d+)$/);
  return match
    ? { name: "detail", id: Number(match[1]) }
    : { name: "dashboard" };
}
