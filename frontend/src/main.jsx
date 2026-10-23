import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Boxes,
  LayoutDashboard,
  Files,
  GitBranch,
  ShieldCheck,
  FileText,
  MessageSquare,
  Plus,
  Download,
  ArrowUpRight,
  ArrowRight,
  ChevronRight,
  ChevronDown,
  Search,
  X,
  Upload,
  FolderOpen,
  FlaskConical,
  Check,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Loader2,
  Sparkles,
  Terminal,
  Code2,
  Braces,
  Network,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Send,
  BookOpen,
  Layers,
  Activity,
  Clock,
  ExternalLink,
  Copy,
} from "lucide-react";
import "./style.css";

const NAV = [
  ["overview", "Overview", LayoutDashboard],
  ["explorer", "Source explorer", Files],
  ["architecture", "Architecture", GitBranch],
  ["quality", "Code quality", ShieldCheck],
  ["documentation", "Documentation", FileText],
  ["ask", "Ask the codebase", MessageSquare],
];
const api = async (path, options = {}) => {
  const response = await fetch("/api" + path, {
    ...options,
    headers:
      options.body instanceof FormData
        ? {}
        : { "Content-Type": "application/json", ...options.headers },
  });
  if (!response.ok) {
    let error;
    try {
      error = await response.json();
    } catch {}
    throw Error(
      typeof error?.detail === "string"
        ? error.detail
        : "The request could not be completed.",
    );
  }
  return response.json();
};
const post = (path, body = {}) =>
  api(path, { method: "POST", body: JSON.stringify(body) });
const number = (n) => new Intl.NumberFormat().format(n ?? 0);
const date = (text) =>
  new Date(text).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
const Spinner = ({ label = "Working…" }) => (
  <span className="working">
    <Loader2 size={16} className="spin" />
    {label}
  </span>
);
const Empty = ({ icon: Icon = Search, title, children }) => (
  <div className="empty">
    <Icon size={32} />
    <h3>{title}</h3>
    <p>{children}</p>
  </div>
);

function App() {
  const [projects, setProjects] = useState([]),
    [active, setActive] = useState(
      localStorage.getItem("codearch-project") || "",
    ),
    [view, setView] = useState("overview"),
    [report, setReport] = useState(null),
    [ai, setAI] = useState(null),
    [modal, setModal] = useState(false),
    [settings, setSettings] = useState(false),
    [error, setError] = useState(""),
    [selectedFile, setSelectedFile] = useState(""),
    [selectedLine, setSelectedLine] = useState(0),
    [loading, setLoading] = useState(true);
  const current = projects.find((p) => p.id === active),
    ready = current?.status === "ready";
  const refresh = async () => {
    try {
      const list = await api("/projects");
      setProjects(list);
      setError((old) => (old === "Failed to fetch" ? "" : old));
      if (!list.some((p) => p.id === active) && list.length)
        setActive(list[0].id);
      setLoading(false);
    } catch (e) {
      setError(e.message);
      setLoading(false);
    }
  };
  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, ready ? 15000 : 1500);
    return () => clearInterval(timer);
  }, [active, ready]);
  useEffect(() => {
    api("/ai/status")
      .then(setAI)
      .catch(() => {});
    const timer = setInterval(
      () =>
        api("/ai/status")
          .then(setAI)
          .catch(() => {}),
      20000,
    );
    return () => clearInterval(timer);
  }, []);
  useEffect(() => {
    setReport(null);
    setSelectedFile("");
    setSelectedLine(0);
    if (active) localStorage.setItem("codearch-project", active);
  }, [active]);
  useEffect(() => {
    let cancelled = false;
    if (ready)
      api(`/projects/${active}/analysis`)
        .then((data) => {
          if (!cancelled) {
            setReport(data);
            setSelectedFile((old) => old || data.modules[0]?.file || "");
          }
        })
        .catch((e) => setError(e.message));
    return () => {
      cancelled = true;
    };
  }, [active, current?.status, current?.updated_at]);
  const openSource = (file, line = 0) => {
    setSelectedFile(file);
    setSelectedLine(line);
    setView("explorer");
  };
  const created = (project) => {
    setActive(project.id);
    setModal(false);
    setView("overview");
    refresh();
  };
  const retry = async () => {
    try {
      await post(`/projects/${active}/reanalyze`);
      setReport(null);
      refresh();
    } catch (e) {
      setError(e.message);
    }
  };
  const projectProps = {
    active,
    report,
    ai,
    openSource,
    setError,
    setSettings,
  };
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="/" aria-label="CodeArchaeologist home">
          <div className="brand-mark">
            <Layers size={27} />
          </div>
          <span>
            Code<span className="brand-second">Archaeologist</span>
            <small>SOURCE INTELLIGENCE</small>
          </span>
        </a>
        <div className="sidebar-label">WORKSPACE</div>
        <button className="workspace-chip" onClick={() => setModal(true)}>
          <span className="workspace-avatar">CA</span>
          <span>
            Capstone workspace<small>Local edition</small>
          </span>
          <ChevronDown size={15} />
        </button>
        <div className="sidebar-label nav-label">EXPLORE</div>
        <nav aria-label="Main navigation">
          {NAV.map(([key, label, Icon]) => (
            <button
              key={key}
              className={"nav-item " + (view === key ? "selected" : "")}
              onClick={() => setView(key)}
            >
              <Icon size={18} />
              <span>{label}</span>
              {key === "ask" && <span className="ai-tag">AI</span>}
            </button>
          ))}
        </nav>
        <div className="sidebar-foot">
          <div className="private-note">
            <ShieldCheck size={17} />
            <div>
              Built to stay local
              <small>Your source stays on this computer.</small>
            </div>
          </div>
          <button className="model-state" onClick={() => setSettings(true)}>
            <span
              className={
                "status-dot " + (ai?.generation.ready ? "green" : "amber")
              }
            />
            <span>
              {ai?.generation.ready ? "Local AI connected" : "AI setup"}
              <small>
                {ai?.embeddings.ready
                  ? "Semantic search ready"
                  : "Check model status"}
              </small>
            </span>
            <ChevronRight size={15} />
          </button>
          <div className="version">
            CodeArchaeologist <span>v1.0</span>
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumb">
            Workspace <ChevronRight size={14} />
            <strong>{NAV.find((n) => n[0] === view)?.[1]}</strong>
          </div>
          <div className="topbar-right">
            <span className="local-label">
              <span className="status-dot green" />
              LOCAL WORKSPACE
            </span>
            <button
              className="avatar"
              aria-label="AI model status"
              onClick={() => setSettings(true)}
            >
              CA
            </button>
          </div>
        </header>
        <main className="main-content">
          <div className="project-toolbar">
            <div className="project-selector">
              <FolderOpen size={18} />
              <select
                aria-label="Select project"
                value={active}
                onChange={(e) => setActive(e.target.value)}
              >
                <option value="" disabled>
                  Select a project
                </option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                    {p.source_kind === "demo" ? " · sample" : ""}
                  </option>
                ))}
              </select>
            </div>
            <div className="toolbar-actions">
              {ready && (
                <button
                  className="button secondary"
                  onClick={retry}
                  title="Reanalyze the stored source and rebuild the search index"
                >
                  <RefreshCw size={14} />
                  Reanalyze
                </button>
              )}
              {ready && (
                <a
                  className="button secondary"
                  href={`/api/projects/${active}/export`}
                >
                  <Download size={15} />
                  Export report
                </a>
              )}
              <button className="button primary" onClick={() => setModal(true)}>
                <Plus size={16} />
                New analysis
              </button>
            </div>
          </div>
          {error && (
            <div className="alert error" role="alert">
              <AlertCircle size={18} />
              <span>{error}</span>
              <button aria-label="Dismiss error" onClick={() => setError("")}>
                <X size={16} />
              </button>
            </div>
          )}
          {loading ? (
            <Empty title="Opening your workspace" icon={Loader2}>
              Loading saved analyses…
            </Empty>
          ) : !current ? (
            <div className="welcome">
              <span className="eyebrow">CODE INTELLIGENCE, WITH CONTEXT</span>
              <h1>
                Every codebase
                <br />
                has a story.
              </h1>
              <p>
                Uncover its structure, understand its behavior, and turn
                unfamiliar Python code into useful knowledge.
              </p>
              <button className="button primary" onClick={() => setModal(true)}>
                Start your first analysis <ArrowRight size={17} />
              </button>
            </div>
          ) : !ready ? (
            <div className="progress-panel">
              <div className="progress-icon">
                {current.status === "failed" ? (
                  <AlertCircle />
                ) : (
                  <Loader2 className="spin" />
                )}
              </div>
              <h1>
                {current.status === "failed"
                  ? "Analysis needs attention"
                  : "Uncovering your codebase"}
              </h1>
              <p>{current.error || current.stage}</p>
              {current.status === "failed" && (
                <button className="button primary" onClick={retry}>
                  <RefreshCw size={16} />
                  Retry analysis
                </button>
              )}
              <small>Projects are analyzed from a local source snapshot.</small>
            </div>
          ) : !report ? (
            <Spinner label="Loading analysis…" />
          ) : (
            <>
              {view === "overview" && (
                <Overview
                  {...projectProps}
                  project={current}
                  setView={setView}
                />
              )}
              {view === "explorer" && (
                <Explorer
                  key={active}
                  {...projectProps}
                  file={selectedFile}
                  setFile={setSelectedFile}
                  line={selectedLine}
                  setLine={setSelectedLine}
                />
              )}
              {view === "architecture" && (
                <Architecture key={active} {...projectProps} />
              )}
              {view === "quality" && <Quality {...projectProps} />}
              {view === "documentation" && (
                <Documentation key={active} {...projectProps} />
              )}
              {view === "ask" && <Ask key={active} {...projectProps} />}
            </>
          )}
          <footer className="page-footer">
            <span>
              <Layers size={13} />
              Structure first. Insight follows.
            </span>
            <span>Python · AST analysis · Local AI</span>
          </footer>
        </main>
      </div>
      {modal && <NewAnalysis close={() => setModal(false)} created={created} />}
      {settings && (
        <ModelStatus
          ai={ai}
          close={() => setSettings(false)}
          refresh={() => api("/ai/status").then(setAI)}
        />
      )}
    </div>
  );
}

function PageHeading({ eyebrow, title, children, action }) {
  return (
    <div className="page-heading">
      <div>
        <span className="eyebrow">{eyebrow}</span>
        <h1>{title}</h1>
        <p>{children}</p>
      </div>
      {action}
    </div>
  );
}

function Overview({ report, project, setView, openSource, ai, setSettings }) {
  const s = report.summary,
    hotspots = [...report.functions]
      .sort((a, b) => b.complexity - a.complexity)
      .slice(0, 4);
  return (
    <>
      <PageHeading
        eyebrow="YOUR CODEBASE, UNCOVERED"
        title="A clearer view of your code."
      >
        Explore the structure, connections, and maintenance signals inside{" "}
        <strong>{project.name}</strong>.
      </PageHeading>
      <div className="analysis-meta">
        <span className="badge success">
          <Check size={12} />
          Analysis complete
        </span>
        <span>
          {project.source_kind === "demo"
            ? "REFERENCE PROJECT"
            : "SOURCE SNAPSHOT"}
        </span>
        <span>
          <Clock size={13} />
          {date(project.updated_at)}
        </span>
        <span>
          {project.retrieval_mode === "semantic"
            ? "Semantic index ready"
            : "Keyword index ready"}
        </span>
      </div>
      <div className="stats-grid">
        {[
          [
            Files,
            "Python modules",
            s.modules,
            `${number(s.lines_of_code)} lines of source`,
          ],
          [
            Braces,
            "Functions & methods",
            s.functions,
            `${s.classes} classes discovered`,
          ],
          [
            Network,
            "Resolved calls",
            s.call_edges,
            `${s.unresolved_calls} calls remain unresolved`,
          ],
          [
            Activity,
            "Average complexity",
            s.average_complexity,
            `${report.quality.high_complexity.length} high-complexity functions`,
          ],
        ].map(([Icon, label, value, detail]) => (
          <article className="stat-card" key={label}>
            <div>
              <span>{label}</span>
              <Icon size={19} />
            </div>
            <strong>{number(value)}</strong>
            <small>{detail}</small>
          </article>
        ))}
      </div>
      <div className="overview-grid">
        <section className="panel architecture-preview">
          <div className="panel-heading">
            <div>
              <h2>Architecture at a glance</h2>
              <p>How the modules connect.</p>
            </div>
            <button
              className="text-button"
              onClick={() => setView("architecture")}
            >
              Explore graph <ArrowUpRight size={16} />
            </button>
          </div>
          <Graph report={report} compact openSource={openSource} />
          <div className="graph-legend">
            <span>
              <i />
              Python module
            </span>
            <span>
              <span className="legend-line" />
              Import dependency
            </span>
          </div>
        </section>
        <section className="panel findings-preview">
          <div className="panel-heading">
            <div>
              <h2>Worth a closer look</h2>
              <p>Signals to guide your review.</p>
            </div>
            <ShieldCheck size={20} />
          </div>
          <button className="finding-row" onClick={() => setView("quality")}>
            <span className="finding-icon amber-bg">
              <Braces size={18} />
            </span>
            <span>
              <strong>
                {s.likely_dead_functions} potentially unused functions
              </strong>
              <small>No resolved incoming call was found.</small>
            </span>
            <ChevronRight size={17} />
          </button>
          <button className="finding-row" onClick={() => setView("quality")}>
            <span className="finding-icon teal-bg">
              <GitBranch size={18} />
            </span>
            <span>
              <strong>{s.unresolved_calls} unresolved calls</strong>
              <small>Dynamic or external calls need context.</small>
            </span>
            <ChevronRight size={17} />
          </button>
          <button className="finding-row" onClick={() => setView("quality")}>
            <span className="finding-icon gray-bg">
              <AlertCircle size={18} />
            </span>
            <span>
              <strong>{s.syntax_errors} files with parse errors</strong>
              <small>
                {s.syntax_errors
                  ? "Open quality findings for details."
                  : "All discovered files parsed successfully."}
              </small>
            </span>
            <ChevronRight size={17} />
          </button>
          <div className="review-note">
            Static findings are review candidates. Check the source before
            making changes.
          </div>
        </section>
      </div>
      <div className="overview-bottom">
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>Complexity spotlight</h2>
              <p>Functions with the most decision points.</p>
            </div>
            <button className="text-button" onClick={() => setView("explorer")}>
              Browse source <ArrowUpRight size={16} />
            </button>
          </div>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Function</th>
                  <th>Module</th>
                  <th>Complexity</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {hotspots.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <Code2 size={14} />
                      <button
                        className="symbol-link"
                        onClick={() => openSource(item.file, item.line_start)}
                      >
                        {item.qualified_name}
                      </button>
                    </td>
                    <td className="muted mono">{item.module}</td>
                    <td>
                      <span
                        className={
                          "score " + (item.complexity >= 8 ? "score-warn" : "")
                        }
                      >
                        {item.complexity}
                      </span>
                    </td>
                    <td>
                      <button
                        className="icon-button"
                        aria-label={"Open " + item.qualified_name}
                        onClick={() => openSource(item.file, item.line_start)}
                      >
                        <ArrowUpRight size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!hotspots.length && (
              <Empty title="No functions found">
                This project contains no extractable functions.
              </Empty>
            )}
          </div>
        </section>
        <section className="ask-promo">
          <span className="sparkle-mark">
            <Sparkles size={24} />
          </span>
          <span className="eyebrow">FROM STRUCTURE TO UNDERSTANDING</span>
          <h2>
            Your code has answers.
            <br />
            Ask the right questions.
          </h2>
          <p>
            Find relevant source and get an explanation grounded in the code.
          </p>
          <button className="button dark" onClick={() => setView("ask")}>
            Ask the codebase <ArrowRight size={16} />
          </button>
          <small>
            {ai?.generation.ready
              ? "Local model connected"
              : "Search is available. Set up local AI for generated answers."}
          </small>
        </section>
      </div>
    </>
  );
}

function Graph({ report, compact = false, mode = "modules", openSource }) {
  const [zoom, setZoom] = useState(1),
    [filter, setFilter] = useState("");
  const isCalls = mode === "calls",
    all = isCalls
      ? report.call_graph.nodes
      : report.modules.map((m) => ({
          id: m.name,
          label: m.name,
          module: m.name,
          kind: "module",
        }));
  const rawEdges = isCalls
    ? report.call_graph.edges
    : report.module_dependencies;
  const filtered = all.filter((n) => !filter || n.module === filter);
  const degree = {};
  for (const e of rawEdges) {
    degree[e.source] = (degree[e.source] || 0) + 1;
    degree[e.target] = (degree[e.target] || 0) + 1;
  }
  const nodes = [...filtered]
    .sort((a, b) => (degree[b.id] || 0) - (degree[a.id] || 0))
    .slice(0, compact ? 9 : 60);
  const cols = compact
      ? Math.min(3, Math.max(nodes.length, 1))
      : Math.min(4, Math.max(nodes.length, 1)),
    nodeW = compact ? 160 : 190,
    nodeH = 56,
    gapX = compact ? 50 : 65,
    gapY = compact ? 42 : 58,
    pad = compact ? 30 : 45;
  const width = Math.max(500, cols * (nodeW + gapX) - gapX + pad * 2),
    height = Math.max(
      compact ? 260 : 410,
      Math.ceil(nodes.length / cols) * (nodeH + gapY) - gapY + pad * 2,
    );
  const positions = {};
  nodes.forEach((n, i) => {
    positions[n.id] = {
      x: pad + (i % cols) * (nodeW + gapX),
      y: pad + Math.floor(i / cols) * (nodeH + gapY),
    };
  });
  const edges = rawEdges.filter(
    (e) => positions[e.source] && positions[e.target],
  );
  const open = (node) => {
    const m = report.modules.find((m) => m.name === node.module);
    const f = report.functions.find((f) => f.id === node.id);
    if (m) openSource(m.file, f?.line_start || 1);
  };
  return (
    <div className={"graph " + (compact ? "compact" : "")}>
      {!compact && (
        <div className="graph-toolbar">
          <label>
            Module{" "}
            <select
              aria-label="Filter graph by module"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            >
              <option value="">All modules</option>
              {report.modules.map((m) => (
                <option key={m.name}>{m.name}</option>
              ))}
            </select>
          </label>
          <span>
            {nodes.length} nodes · {edges.length} edges
            {filtered.length > nodes.length
              ? ` · ${filtered.length - nodes.length} hidden`
              : ""}
          </span>
          <div>
            <button
              className="icon-button"
              aria-label="Zoom out"
              onClick={() => setZoom((z) => Math.max(0.5, z - 0.15))}
            >
              <ZoomOut size={17} />
            </button>
            <button
              className="icon-button"
              aria-label="Zoom in"
              onClick={() => setZoom((z) => Math.min(2, z + 0.15))}
            >
              <ZoomIn size={17} />
            </button>
            <button
              className="icon-button"
              aria-label="Reset graph zoom"
              onClick={() => setZoom(1)}
            >
              <Maximize2 size={17} />
            </button>
          </div>
        </div>
      )}
      <div className="graph-canvas">
        <svg
          role="img"
          aria-label={
            isCalls ? "Function call graph" : "Module dependency graph"
          }
          viewBox={`0 0 ${width} ${height}`}
          style={{
            width: compact ? "100%" : width * zoom,
            minWidth: compact ? undefined : width * zoom,
          }}
        >
          <defs>
            <marker
              id={compact ? "arrow-small" : "arrow-large"}
              viewBox="0 0 10 10"
              refX="9"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#91a6aa" />
            </marker>
          </defs>
          {edges.map((e, i) => {
            const s = positions[e.source],
              t = positions[e.target];
            const same = s.x === t.x;
            const x1 = s.x + nodeW / 2,
              y1 = s.y + nodeH,
              x2 = t.x + nodeW / 2,
              y2 = t.y;
            return (
              <path
                key={i}
                d={
                  same
                    ? `M${x1},${y1} C${x1 + 65},${y1 + 30} ${x2 + 65},${y2 - 30} ${x2},${y2}`
                    : `M${s.x + nodeW},${s.y + nodeH / 2} C${s.x + nodeW + 45},${s.y + nodeH / 2} ${t.x - 45},${t.y + nodeH / 2} ${t.x},${t.y + nodeH / 2}`
                }
                fill="none"
                stroke="#a4b5b6"
                strokeWidth="1.5"
                markerEnd={`url(#${compact ? "arrow-small" : "arrow-large"})`}
              />
            );
          })}
          {nodes.map((n) => {
            const p = positions[n.id],
              label = n.label.split(".").at(-1),
              short = label.length > 21 ? label.slice(0, 19) + "…" : label;
            return (
              <g
                key={n.id}
                transform={`translate(${p.x},${p.y})`}
                role="button"
                tabIndex={0}
                aria-label={"Open " + n.label}
                onClick={() => open(n)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") open(n);
                }}
                className="graph-node"
              >
                <title>{n.label}</title>
                <rect width={nodeW} height={nodeH} rx="8" />
                <rect
                  x="0"
                  width="4"
                  height={nodeH}
                  rx="2"
                  className="node-accent"
                />
                <text x="17" y="23" className="node-label">
                  {short}
                </text>
                <text x="17" y="41" className="node-kind">
                  {n.kind === "module"
                    ? "Python module"
                    : n.kind?.replaceAll("_", " ")}
                </text>
              </g>
            );
          })}
          {!nodes.length && (
            <text x="40" y="80">
              No nodes match this selection.
            </text>
          )}
        </svg>
      </div>
    </div>
  );
}

function Architecture(props) {
  const [mode, setMode] = useState("modules");
  return (
    <>
      <PageHeading
        eyebrow="FOLLOW THE CONNECTIONS"
        title="Architecture, made visible."
      >
        Explore imports and resolved calls. Select any node to inspect its
        source.
      </PageHeading>
      <div className="tab-row">
        <button
          className={mode === "modules" ? "active" : ""}
          onClick={() => setMode("modules")}
        >
          <Boxes size={16} />
          Module dependencies
        </button>
        <button
          className={mode === "calls" ? "active" : ""}
          onClick={() => setMode("calls")}
        >
          <Network size={16} />
          Function call graph
        </button>
      </div>
      <section className="panel">
        <Graph {...props} mode={mode} />
      </section>
      <div className="info-line">
        <AlertCircle size={16} />
        Call resolution is static and best-effort. External libraries,
        callbacks, and dynamic dispatch may remain unresolved.
      </div>
    </>
  );
}

function Explorer({
  active,
  report,
  file,
  setFile,
  line,
  setLine,
  ai,
  setSettings,
  setError,
}) {
  const [source, setSource] = useState(null),
    [filter, setFilter] = useState(""),
    [explanation, setExplanation] = useState(null),
    [busy, setBusy] = useState(false);
  const sourceRef = useRef(null);
  useEffect(() => {
    let cancelled = false;
    setSource(null);
    setExplanation(null);
    if (file)
      api(`/projects/${active}/source?file=${encodeURIComponent(file)}`)
        .then((data) => {
          if (!cancelled) setSource(data);
        })
        .catch((e) => setError(e.message));
    return () => {
      cancelled = true;
    };
  }, [active, file]);
  useEffect(() => {
    if (source && line)
      sourceRef.current
        ?.querySelector(`[data-line="${line}"]`)
        ?.scrollIntoView({ block: "center", behavior: "smooth" });
  }, [source, line]);
  const symbols = [...report.classes, ...report.functions].filter(
      (f) => f.file === file,
    ),
    selected = symbols.find((s) => s.line_start === line);
  const explain = async () => {
    if (!ai?.generation.ready) {
      setSettings(true);
      return;
    }
    setBusy(true);
    try {
      const target =
        selected?.id || report.modules.find((m) => m.file === file)?.name;
      setExplanation(
        await post(`/projects/${active}/explain`, { symbol_id: target }),
      );
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <>
      <PageHeading eyebrow="READ WITH CONTEXT" title="Source explorer.">
        Browse files, jump to symbols, and explain the code you’re looking at.
      </PageHeading>
      <div className="explorer-layout">
        <aside className="file-panel panel">
          <div className="file-filter">
            <Search size={15} />
            <input
              aria-label="Filter source files"
              placeholder="Find a file…"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            />
          </div>
          <div className="file-list">
            {report.modules
              .filter((m) =>
                m.file.toLowerCase().includes(filter.toLowerCase()),
              )
              .map((m) => (
                <button
                  key={m.file}
                  title={m.file}
                  className={file === m.file ? "active" : ""}
                  onClick={() => {
                    setFile(m.file);
                    setLine(0);
                  }}
                >
                  <FileText size={15} />
                  <span>{m.file}</span>
                  {m.syntax_error && <AlertCircle size={13} />}
                </button>
              ))}
          </div>
          <div className="symbols-heading">SYMBOLS IN THIS FILE</div>
          <div className="symbol-list">
            {symbols.map((s) => (
              <button
                key={s.id}
                onClick={() => setLine(s.line_start)}
                className={line === s.line_start ? "active" : ""}
              >
                <span className="symbol-kind">{s.kind ? "ƒ" : "C"}</span>
                <span>{s.qualified_name}</span>
                <small>{s.line_start}</small>
              </button>
            ))}
            {!symbols.length && (
              <p className="muted small-text">No symbols in this file.</p>
            )}
          </div>
        </aside>
        <div className="source-column">
          <section className="source-panel">
            <div className="source-header">
              <span>
                <Code2 size={16} />
                {file}
              </span>
              <button
                className="button secondary small-button"
                disabled={busy}
                onClick={explain}
              >
                {busy ? (
                  <Spinner label="Explaining…" />
                ) : (
                  <>
                    <Sparkles size={14} />
                    Explain {selected ? "symbol" : "file"}
                  </>
                )}
              </button>
            </div>
            <div ref={sourceRef} className="source-lines">
              {source ? (
                source.content.split("\n").map((text, i) => (
                  <div
                    key={i}
                    data-line={i + 1}
                    className={
                      "source-line " + (line === i + 1 ? "highlight" : "")
                    }
                  >
                    <span className="line-number">{i + 1}</span>
                    <code>{text || " "}</code>
                  </div>
                ))
              ) : (
                <Spinner label="Loading source…" />
              )}
            </div>
          </section>
          {selected && (
            <div className="symbol-detail">
              <span className="badge">{selected.kind || "class"}</span>
              <strong>{selected.qualified_name}</strong>
              <span>
                Lines {selected.line_start}–{selected.line_end}
              </span>
              {selected.complexity && (
                <span>Complexity {selected.complexity}</span>
              )}
            </div>
          )}
          {explanation && (
            <section className="panel explanation-panel">
              <div className="panel-heading">
                <h2>
                  <Sparkles size={18} />
                  AI explanation
                </h2>
                <span className="badge">{explanation.provider}</span>
              </div>
              <div className="markdown">
                <Markdown remarkPlugins={[remarkGfm]}>
                  {explanation.answer}
                </Markdown>
              </div>
              <p className="muted small-text">
                AI interpretation. Check claims against the displayed source.
              </p>
            </section>
          )}
        </div>
      </div>
    </>
  );
}

function Quality({ report, openSource }) {
  const [filter, setFilter] = useState("unused");
  const groups = {
    unused: [
      ...report.dead_code.functions.map((f) => ({
        ...f,
        finding: "Potentially unused function",
      })),
      ...report.dead_code.classes.map((c) => ({
        ...c,
        finding: "Potentially unused class",
      })),
    ],
    complexity: report.quality.high_complexity.map((f) => ({
      ...f,
      finding: `Complexity ${f.complexity}`,
    })),
    long: report.quality.long_functions.map((f) => ({
      ...f,
      finding: `${f.loc} lines`,
    })),
    unresolved: report.unresolved_calls.map((f, i) => ({
      ...f,
      id: i,
      qualified_name: f.call,
      line_start: f.line,
      finding: "Unresolved call",
    })),
    syntax: report.quality.syntax_errors.map((m) => ({
      ...m,
      id: m.name,
      qualified_name: m.name,
      line_start: 1,
      finding: m.syntax_error,
    })),
  };
  return (
    <>
      <PageHeading eyebrow="REVIEW WHAT MATTERS" title="Code quality signals.">
        Prioritize maintenance with source-linked findings and transparent
        limitations.
      </PageHeading>
      <div className="tab-row scroll-tabs">
        {[
          ["unused", "Potentially unused"],
          ["complexity", "High complexity"],
          ["long", "Long functions"],
          ["unresolved", "Unresolved calls"],
          ["syntax", "Parse errors"],
        ].map(([key, label]) => (
          <button
            key={key}
            className={filter === key ? "active" : ""}
            onClick={() => setFilter(key)}
          >
            {label}
            <span>{groups[key].length}</span>
          </button>
        ))}
      </div>
      <section className="panel">
        <div className="panel-heading">
          <div>
            <h2>
              {filter === "unused"
                ? "Candidates for review"
                : filter === "unresolved"
                  ? "Calls needing more context"
                  : "Source findings"}
            </h2>
            <p>
              {filter === "unused"
                ? "No resolved incoming calls were found. Framework entry points and dynamic usage may still use these symbols."
                : filter === "complexity"
                  ? "Functions with estimated cyclomatic complexity of 8 or more."
                  : filter === "long"
                    ? "Functions spanning 60 or more source lines."
                    : filter === "unresolved"
                      ? "These calls may refer to external APIs, dynamic objects, or unsupported patterns."
                      : "Files that could not be parsed are retained in the source explorer."}
            </p>
          </div>
        </div>
        {groups[filter].length ? (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Source</th>
                  <th>Finding</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {groups[filter].map((item, i) => (
                  <tr key={item.id + "-" + i}>
                    <td>
                      <button
                        className="symbol-link"
                        onClick={() => openSource(item.file, item.line_start)}
                      >
                        {item.qualified_name}
                      </button>
                    </td>
                    <td className="mono muted">
                      {item.file}:{item.line_start}
                    </td>
                    <td>
                      <span className="finding-text">{item.finding}</span>
                    </td>
                    <td>
                      <button
                        className="icon-button"
                        aria-label={"Inspect " + item.qualified_name}
                        onClick={() => openSource(item.file, item.line_start)}
                      >
                        <ArrowUpRight size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty icon={CheckCircle2} title="No findings in this category">
            Other categories may still contain useful review signals.
          </Empty>
        )}
      </section>
      <div className="info-line">
        <ShieldCheck size={17} />
        This tool never edits or executes the code you import.
      </div>
    </>
  );
}

function Documentation({
  active,
  report,
  ai,
  setSettings,
  setError,
  openSource,
}) {
  const [docs, setDocs] = useState(null),
    [busy, setBusy] = useState(false),
    [selected, setSelected] = useState(null);
  const load = () =>
    api(`/projects/${active}/documentation`)
      .then(setDocs)
      .catch((e) => setError(e.message));
  useEffect(() => {
    setSelected(null);
    load();
  }, [active]);
  const generate = async () => {
    if (!ai?.generation.ready) {
      setSettings(true);
      return;
    }
    setBusy(true);
    try {
      const result = await post(`/projects/${active}/explain`);
      setSelected(result);
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };
  const answer = selected?.answer || selected?.content;
  return (
    <>
      <PageHeading
        eyebrow="KNOWLEDGE THAT TRAVELS"
        title="Documentation from the source."
        action={
          <button className="button primary" onClick={generate} disabled={busy}>
            {busy ? (
              <Spinner label="Generating…" />
            ) : (
              <>
                <Sparkles size={16} />
                Generate AI overview
              </>
            )}
          </button>
        }
      >
        Export structured analysis and module reference docs. Add an AI overview
        when the local model is connected.
      </PageHeading>
      <div className="documentation-layout">
        <aside className="panel docs-nav">
          <h3>PROJECT DOCUMENTATION</h3>
          <button
            className={!selected ? "active" : ""}
            onClick={() => setSelected(null)}
          >
            <BookOpen size={16} />
            Static analysis summary
          </button>
          {docs?.explanations.map((note) => (
            <button
              key={note.id}
              className={selected?.id === note.id ? "active" : ""}
              onClick={() => setSelected(note)}
            >
              <Sparkles size={16} />
              <span>
                {note.target === "overview"
                  ? "AI project overview"
                  : note.target}
              </span>
              <small>{date(note.created_at)}</small>
            </button>
          ))}
          <div className="docs-export">
            <Download size={20} />
            <h3>Take your findings with you.</h3>
            <p>JSON, Markdown, diagrams, and saved AI notes in one ZIP.</p>
            <a
              className="button secondary"
              href={`/api/projects/${active}/export`}
            >
              Download report
            </a>
          </div>
        </aside>
        <section className="panel docs-content">
          {docs ? (
            <>
              <div className="doc-status">
                <span className="badge">
                  {selected ? "AI interpretation" : "STATIC ANALYSIS"}
                </span>
                <span>
                  {selected
                    ? "Verify against source references"
                    : "Generated from the parsed codebase"}
                </span>
              </div>
              <div className="markdown">
                <Markdown remarkPlugins={[remarkGfm]}>
                  {answer || docs.markdown}
                </Markdown>
              </div>
              {selected?.citations && (
                <Evidence
                  citations={selected.citations}
                  openSource={openSource}
                />
              )}
            </>
          ) : (
            <Spinner label="Loading documentation…" />
          )}
        </section>
      </div>
    </>
  );
}

function Evidence({ citations, openSource }) {
  return (
    <div className="evidence">
      <h3>SOURCE EVIDENCE</h3>
      {citations.map((c, i) => (
        <button
          key={c.label || c.id || i}
          onClick={() => openSource(c.file, c.line_start)}
        >
          <span className="citation-label">{c.label || i + 1}</span>
          <span>
            <strong>{c.name}</strong>
            <small>
              {c.file}:{c.line_start}–{c.line_end}
            </small>
          </span>
          <ArrowUpRight size={15} />
        </button>
      ))}
    </div>
  );
}

function Ask({ active, ai, setError, setSettings, openSource }) {
  const [query, setQuery] = useState(""),
    [mode, setMode] = useState("ask"),
    [busy, setBusy] = useState(false),
    [result, setResult] = useState(null),
    [history, setHistory] = useState([]);
  useEffect(() => {
    setResult(null);
    api(`/projects/${active}/history`)
      .then(setHistory)
      .catch(() => {});
  }, [active]);
  const submit = async (text) => {
    const q = (text ?? query).trim();
    if (q.length < 3) return;
    if (mode === "ask" && !ai?.generation.ready) {
      setSettings(true);
      return;
    }
    setQuery(q);
    setBusy(true);
    try {
      const data =
        mode === "ask"
          ? await post(`/projects/${active}/ask`, { question: q })
          : await api(`/projects/${active}/search?q=${encodeURIComponent(q)}`);
      setResult({ ...data, question: q });
      if (mode === "ask") setHistory(await api(`/projects/${active}/history`));
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <>
      <PageHeading
        eyebrow="QUESTIONS, GROUNDED IN CODE"
        title="Ask the codebase."
      >
        Search by meaning, inspect the evidence, and let local AI explain what
        it finds.
      </PageHeading>
      <div className="ask-layout">
        <section className="panel conversation">
          <div className="ask-mode">
            <div className="segmented">
              <button
                className={mode === "ask" ? "active" : ""}
                onClick={() => setMode("ask")}
              >
                <Sparkles size={15} />
                Ask AI
              </button>
              <button
                className={mode === "search" ? "active" : ""}
                onClick={() => setMode("search")}
              >
                <Search size={15} />
                Search code
              </button>
            </div>
            <span className="muted small-text">
              {ai?.embeddings.ready
                ? "Semantic retrieval"
                : "Keyword retrieval"}
            </span>
          </div>
          {!result ? (
            <div className="ask-empty">
              <div className="ask-orb">
                <Sparkles size={30} />
              </div>
              <h2>A good question is a great start.</h2>
              <p>
                Ask about behavior, dependencies, or the path through your code.
              </p>
              <div className="suggestions">
                {[
                  "How is the order total calculated?",
                  "Where are notifications sent?",
                  "How does the checkout flow work?",
                ].map((q) => (
                  <button key={q} onClick={() => submit(q)}>
                    {q}
                    <ArrowUpRight size={15} />
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="answer-body">
              <div className="question-bubble">
                <MessageSquare size={16} />
                {result.question}
              </div>
              {result.answer || result.content ? (
                <>
                  <div className="answer-label">
                    <Sparkles size={16} />
                    CodeArchaeologist <span>{result.provider}</span>
                  </div>
                  <div className="markdown">
                    <Markdown remarkPlugins={[remarkGfm]}>
                      {result.answer || result.content}
                    </Markdown>
                  </div>
                  <p className="answer-disclaimer">
                    AI interpretation from retrieved excerpts. Verify important
                    claims in the source.
                  </p>
                </>
              ) : (
                <>
                  <h2>{result.results.length} relevant source results</h2>
                  <p className="muted">
                    {result.mode === "semantic"
                      ? "Learned embeddings combined with exact-term matching."
                      : "Keyword matching. Install the embedding model for semantic search."}
                  </p>
                  {result.results.map((item) => (
                    <button
                      key={item.id}
                      className="search-result"
                      onClick={() => openSource(item.file, item.line_start)}
                    >
                      <strong>
                        {item.name}
                        <ArrowUpRight size={16} />
                      </strong>
                      <span>
                        {item.file}:{item.line_start}–{item.line_end}
                      </span>
                      <pre>{item.content.slice(0, 600)}</pre>
                    </button>
                  ))}
                  {!result.results.length && (
                    <Empty title="No relevant matches">
                      Try a function name or a more specific description.
                    </Empty>
                  )}
                </>
              )}
            </div>
          )}
          <form
            className="question-form"
            onSubmit={(e) => {
              e.preventDefault();
              submit();
            }}
          >
            <textarea
              aria-label="Question about the codebase"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={
                mode === "ask"
                  ? "Ask a question about this codebase…"
                  : "Describe the code you’re looking for…"
              }
              rows={2}
              maxLength={1500}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  submit();
                }
              }}
            />
            <div>
              <span>
                {busy
                  ? "Reading evidence and preparing a response…"
                  : "Enter to send · Shift + Enter for a new line"}
              </span>
              <button
                type="submit"
                className="button primary"
                disabled={busy || query.trim().length < 3}
              >
                {busy ? (
                  <Loader2 size={18} className="spin" />
                ) : (
                  <Send size={18} />
                )}
                <span>{mode === "ask" ? "Ask" : "Search"}</span>
              </button>
            </div>
          </form>
        </section>
        <aside>
          <section className="panel evidence-panel">
            {result?.citations ? (
              <Evidence citations={result.citations} openSource={openSource} />
            ) : (
              <>
                <h3>
                  <ShieldCheck size={16} />
                  Evidence comes first.
                </h3>
                <p>
                  Answers use retrieved source excerpts and static analysis.
                  Source references appear here for inspection.
                </p>
                <div className="evidence-step">
                  <span>1</span>Retrieve relevant code
                </div>
                <div className="evidence-step">
                  <span>2</span>Explain with local AI
                </div>
                <div className="evidence-step">
                  <span>3</span>Verify in the source
                </div>
              </>
            )}
          </section>
          <section className="panel history-panel">
            <h3>
              <Clock size={15} />
              Recent questions
            </h3>
            {history.slice(0, 8).map((note) => (
              <button key={note.id} onClick={() => setResult(note)}>
                {note.question}
                <ChevronRight size={14} />
              </button>
            ))}
            {!history.length && <p>Your saved questions will appear here.</p>}
          </section>
        </aside>
      </div>
    </>
  );
}

function NewAnalysis({ close, created }) {
  const [tab, setTab] = useState("zip"),
    [file, setFile] = useState(null),
    [path, setPath] = useState(""),
    [name, setName] = useState(""),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const fileInput = useRef(null);
  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      let result;
      if (tab === "demo") result = await post("/projects/demo");
      else if (tab === "folder")
        result = await post("/projects/folder", { path, name });
      else {
        if (!file) throw Error("Choose a ZIP file first.");
        const body = new FormData();
        body.append("file", file);
        result = await api("/projects/upload", { method: "POST", body });
      }
      created(result);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <div
      className="modal-backdrop"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget && !busy) close();
      }}
    >
      <section
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="new-analysis-title"
      >
        <button
          className="modal-close icon-button"
          aria-label="Close new analysis"
          onClick={close}
          disabled={busy}
        >
          <X size={20} />
        </button>
        <div className="modal-icon">
          <Layers size={25} />
        </div>
        <span className="eyebrow">START EXPLORING</span>
        <h2 id="new-analysis-title">Uncover a codebase.</h2>
        <p>Import Python source to create a local analysis snapshot.</p>
        <div className="tab-row">
          <button
            className={tab === "zip" ? "active" : ""}
            onClick={() => setTab("zip")}
          >
            <Upload size={15} />
            Upload ZIP
          </button>
          <button
            className={tab === "folder" ? "active" : ""}
            onClick={() => setTab("folder")}
          >
            <FolderOpen size={15} />
            Local folder
          </button>
          <button
            className={tab === "demo" ? "active" : ""}
            onClick={() => setTab("demo")}
          >
            <FlaskConical size={15} />
            Sample project
          </button>
        </div>
        <form onSubmit={submit}>
          {tab === "zip" ? (
            <>
              <input
                type="file"
                accept=".zip"
                aria-label="Choose project ZIP"
                ref={fileInput}
                className="hidden"
                onChange={(e) => setFile(e.target.files[0] || null)}
              />
              <button
                type="button"
                className="dropzone"
                onClick={() => fileInput.current.click()}
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault();
                  setFile(e.dataTransfer.files[0] || null);
                }}
              >
                <Upload size={29} />
                <strong>
                  {file ? file.name : "Drop your project ZIP here"}
                </strong>
                <span>
                  {file
                    ? `${(file.size / 1024 / 1024).toFixed(1)} MB selected`
                    : "or click to choose a file · up to 30 MB"}
                </span>
              </button>
            </>
          ) : tab === "folder" ? (
            <>
              <label className="field-label">
                Project folder
                <input
                  required
                  value={path}
                  onChange={(e) => setPath(e.target.value)}
                  placeholder="C:\Projects\my-python-app"
                />
              </label>
              <label className="field-label">
                Project name <span>(optional)</span>
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="My Python project"
                  maxLength={100}
                />
              </label>
              <p className="small-text muted">
                Use an absolute folder path on the computer running this
                application.
              </p>
            </>
          ) : (
            <div className="demo-card">
              <FlaskConical size={30} />
              <h3>Legacy Shop</h3>
              <p>
                A small Python checkout service with pricing, discounts,
                notifications, and intentionally unused code. A useful starting
                point for your demonstration.
              </p>
            </div>
          )}
          {error && (
            <div className="alert error" role="alert">
              {error}
            </div>
          )}
          <div className="modal-bottom">
            <span>
              <ShieldCheck size={15} />
              Source is parsed, never executed.
            </span>
            <button type="submit" className="button primary" disabled={busy}>
              {busy ? (
                <Spinner label="Importing…" />
              ) : (
                <>
                  Analyze project <ArrowRight size={16} />
                </>
              )}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}

function ModelStatus({ ai, close, refresh }) {
  const [busy, setBusy] = useState(false);
  return (
    <div className="modal-backdrop">
      <section
        className="modal model-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="model-title"
      >
        <button
          className="modal-close icon-button"
          aria-label="Close model status"
          onClick={close}
        >
          <X size={20} />
        </button>
        <div className="modal-icon">
          <Sparkles size={25} />
        </div>
        <span className="eyebrow">YOUR LOCAL AI</span>
        <h2 id="model-title">Connected to your computer.</h2>
        <p>Models run locally. No API key or paid service is required.</p>
        <div className="model-status-row">
          <span
            className={
              "status-dot " + (ai?.generation.ready ? "green" : "amber")
            }
          />
          <div>
            <strong>Code explanation model</strong>
            <p>
              {ai?.generation.ready
                ? ai.generation.model
                : ai?.generation.message || "Checking…"}
            </p>
          </div>
          <span className="badge">
            {ai?.generation.ready ? "Ready" : "Setup needed"}
          </span>
        </div>
        <div className="model-status-row">
          <span
            className={
              "status-dot " + (ai?.embeddings.ready ? "green" : "amber")
            }
          />
          <div>
            <strong>Semantic embeddings</strong>
            <p>{ai?.embeddings.model || "BGE small English"}</p>
          </div>
          <span className="badge">
            {ai?.embeddings.ready ? "Ready" : "Setup needed"}
          </span>
        </div>
        <div className="setup-instructions">
          <h3>First-time setup</h3>
          <ol>
            <li>
              Run <code>INSTALL.bat</code> in the project folder.
            </li>
            <li>
              Run <code>SETUP_AI.bat</code> to download the local models.
            </li>
            <li>
              Start or restart with <code>START.bat</code>.
            </li>
          </ol>
          <p>
            The compact code model is about 718 MB. The embedding weights are
            about 67 MB. A larger model can improve answer quality; see the
            README for Ollama configuration.
          </p>
        </div>
        <button
          className="button primary"
          onClick={async () => {
            setBusy(true);
            try {
              await refresh();
            } finally {
              setBusy(false);
            }
          }}
          disabled={busy}
        >
          {busy ? (
            <Spinner label="Checking…" />
          ) : (
            <>
              <RefreshCw size={16} />
              Check connection
            </>
          )}
        </button>
      </section>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
