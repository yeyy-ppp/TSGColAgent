import { useEffect, useState } from 'react';
import {
  BarChart3, BookOpenCheck, Bot, GitBranch, Layers3, Menu, MessageSquareText,
  Play, RefreshCw, TestTube2, Wifi, WifiOff, Workflow, X,
} from 'lucide-react';
import { connectRuntime, fetchArtifact, fetchKnowledge, fetchRuntime, selectedExperiment } from './api';
import type { Artifact, KnowledgeSnapshot, RuntimeSnapshot } from './types';
import { paperAverages } from './format';
import DetailDrawer, { DataVisual, StateModelVisual, type DetailContent } from './components/DetailDrawer';
import { ChatWorkspace } from './components/ChatWorkspace';
import { ExperimentLauncher } from './components/ExperimentLauncher';
import { ExperimentSwitcher } from './components/ExperimentSwitcher';
import { AgentsPage, KnowledgePage, OverviewPage, PhasesPage, StatePage, SystemPage, TasksPage } from './components/pages';

type View = 'overview' | 'run' | 'agents' | 'phases' | 'state' | 'tasks' | 'knowledge' | 'system';

const nav = [
  { id: 'overview' as const, label: '实验总览', icon: BarChart3 },
  { id: 'run' as const, label: '启动实验', icon: Play },
  { id: 'state' as const, label: '测试状态中心', icon: GitBranch },
  { id: 'agents' as const, label: '多智能体协作台', icon: Bot },
  { id: 'phases' as const, label: '测试生成过程', icon: Workflow },
  { id: 'tasks' as const, label: '任务与报告', icon: TestTube2 },
  { id: 'knowledge' as const, label: '测试知识引导库', icon: BookOpenCheck },
];

const runtimeCache = new Map<string, RuntimeSnapshot>();

function rememberRuntime(id: string, snapshot: RuntimeSnapshot) {
  runtimeCache.delete(id);
  runtimeCache.set(id, snapshot);
  while (runtimeCache.size > 4) {
    const oldest = [...runtimeCache.keys()].find((key) => key !== 'all');
    if (!oldest) break;
    runtimeCache.delete(oldest);
  }
}

function datasetPreview(snapshot: RuntimeSnapshot, id: string): RuntimeSnapshot | null {
  const card = snapshot.experiments.find((item) => item.id === id);
  if (!card) return null;
  const tasks = snapshot.tasks.filter((task) => task.experiment_id === id || task.dataset_id === id || task.dataset_name === card.label || task.experiment_label === card.label);
  if (!tasks.length) return null;
  const gradeCounts = Object.fromEntries(['A', 'B', 'C', 'D', 'E'].map((grade) => [grade, tasks.filter((task) => task.grade === grade).length]));
  const valid = tasks.filter((task) => ['A', 'B', 'C'].includes(task.grade) && task.metrics.tests_passed);
  const average = (key: keyof (typeof valid)[number]['metrics']) => {
    const values = valid.map((task) => task.metrics[key]).filter((value): value is number => typeof value === 'number');
    return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : undefined;
  };
  return {
    ...snapshot,
    experiment: { id: card.id, output_dir: card.output_dir, label: card.label, registered_at: '', status: card.status || 'completed', started_at: card.started_at, finished_at: card.finished_at, duration_seconds: card.duration_seconds },
    portfolio: undefined,
    tasks,
    current_task: tasks[0],
    overview: {
      ...snapshot.overview,
      language: card.language,
      scope: card.scope,
      status: card.status || 'completed',
      total_tasks: card.total_tasks || tasks.length,
      completed_execution: Number(gradeCounts.A) + Number(gradeCounts.B) + Number(gradeCounts.C),
      not_completed_execution: Number(gradeCounts.D) + Number(gradeCounts.E),
      grade_counts: gradeCounts,
      completion_rate: tasks.length ? (Number(gradeCounts.A) + Number(gradeCounts.B) + Number(gradeCounts.C)) / tasks.length : 0,
      quality_averages: { average_line_coverage: average('line_coverage') ?? '—', average_branch_coverage: average('branch_coverage') ?? '—', average_ae: average('ae') ?? '—', average_mutation_score: average('mutation_score') ?? '—', ...paperAverages(tasks, card.total_tasks || tasks.length) },
      started_at: card.started_at,
      finished_at: card.finished_at,
      duration_seconds: card.duration_seconds,
    },
  };
}

export default function App() {
  const [view, setView] = useState<View>('overview');
  const [experimentId, setExperimentId] = useState(selectedExperiment());
  const [runtime, setRuntime] = useState<RuntimeSnapshot | null>(null);
  const [knowledge, setKnowledge] = useState<KnowledgeSnapshot | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState('');
  const [detail, setDetail] = useState<DetailContent | null>(null);
  const [chatOpen, setChatOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    let alive = true;
    let stream: EventSource | null = null;
    const request = new AbortController();
    const cached = runtimeCache.get(experimentId);
    if (cached) setRuntime(cached);
    setConnected(false);
    fetchRuntime(experimentId, request.signal).then((data) => {
      if (!alive) return;
      rememberRuntime(experimentId, data);
      setRuntime(data);
      setError('');
      const status = String(data.overview.status || '').toLowerCase();
      if (!['running', 'queued', 'waiting'].includes(status)) {
        setConnected(true);
        return;
      }
      stream = connectRuntime(experimentId, (next) => {
        if (!alive) return;
        rememberRuntime(experimentId, next);
        setRuntime(next);
        setConnected(true);
        setError('');
      }, () => alive && setConnected(false));
    }).catch((cause) => alive && cause instanceof DOMException && cause.name === 'AbortError' ? undefined : alive && setError(String(cause)));
    return () => { alive = false; request.abort(); stream?.close(); };
  }, [experimentId]);

  useEffect(() => {
    if (view !== 'knowledge') return undefined;
    let alive = true;
    const request = new AbortController();
    const refresh = () => fetchKnowledge(experimentId, request.signal).then((data) => alive && setKnowledge(data)).catch(() => undefined);
    refresh(); const timer = window.setInterval(refresh, 15000);
    return () => { alive = false; request.abort(); window.clearInterval(timer); };
  }, [experimentId, view]);

  function selectExperiment(id: string) {
    const cached = runtimeCache.get(id);
    const source = runtimeCache.get('all') || runtime;
    const preview = !cached && source && id !== 'all' ? datasetPreview(source, id) : null;
    if (cached) setRuntime(cached);
    else if (preview) { rememberRuntime(id, preview); setRuntime(preview); }
    setExperimentId(id);
    const url = new URL(window.location.href);
    if (id) url.searchParams.set('experiment', id); else url.searchParams.delete('experiment');
    window.history.replaceState({}, '', url);
  }

  async function openArtifact(path: string) {
    if (!runtime?.experiment?.id) return;
    setDetail({ title: '正在读取文件', body: <p>{path}</p> });
    try {
      const artifact: Artifact = await fetchArtifact(runtime.experiment.id, path);
      if (artifact.kind === 'state_model' && artifact.state_model) {
        setDetail({ title: '测试状态中心', eyebrow: `${artifact.size.toLocaleString()} 字节 · 专用可视化`, body: <StateModelVisual model={artifact.state_model} path={artifact.path} /> });
        return;
      }
      if (artifact.kind === 'data') {
        setDetail({ title: artifact.name, eyebrow: `${artifact.size.toLocaleString()} 字节 · 数据视图`, body: <DataVisual data={artifact.data} title="报告内容" /> });
        return;
      }
      if (artifact.kind === 'html' && artifact.content) {
        setDetail({ title: artifact.name, eyebrow: `${artifact.size.toLocaleString()} 字节 · 报告页面`, body: <iframe className="artifact-report-frame" title={artifact.name} sandbox="" srcDoc={artifact.content} /> });
        return;
      }
      setDetail({ title: artifact.name, eyebrow: `${artifact.size.toLocaleString()} 字节`, body: <>{artifact.truncated && <p className="detail-note">文件较大，当前展示前200,000个字符；原始文件保持完整。</p>}<pre className="artifact-content">{artifact.content || '文件内容为空'}</pre></>, raw: { path: artifact.path, size: artifact.size } });
    } catch (cause) { setDetail({ title: '无法读取文件', body: <p>{String(cause)}</p>, raw: { path } }); }
  }

  function go(next: View) { setView(next); setMenuOpen(false); }
  const content = runtime ? <>
    {view === 'overview' && <OverviewPage runtime={runtime} open={setDetail} />}
    {view === 'run' && <ExperimentLauncher runtime={runtime} open={setDetail} onStarted={() => { selectExperiment('all'); setView('overview'); }} />}
    {view === 'agents' && <AgentsPage runtime={runtime} open={setDetail} />}
    {view === 'phases' && <PhasesPage runtime={runtime} open={setDetail} />}
    {view === 'state' && <StatePage runtime={runtime} open={setDetail} />}
    {view === 'tasks' && <TasksPage runtime={runtime} open={setDetail} openArtifact={openArtifact} />}
    {view === 'knowledge' && <KnowledgePage knowledge={knowledge} open={setDetail} />}
    {view === 'system' && <SystemPage runtime={runtime} open={setDetail} />}
  </> : <div className="loading-state"><RefreshCw className="spin" /><h2>正在连接智能体系统</h2><p>{error || '读取实验注册表与实时状态'}</p></div>;

  return <div className={`app-shell ${chatOpen ? 'chat-visible' : ''}`}>
    <aside className={`sidebar ${menuOpen ? 'open' : ''}`}>
      <div className="brand"><span><Layers3 /></span><div><b>ValiFixTest &amp; TSGColAgent</b><small>测试状态引导多智能体方法</small></div><button className="sidebar-close" onClick={() => setMenuOpen(false)}><X /></button></div>
      <nav>{nav.map(({ id, label, icon: Icon }) => <button key={id} className={view === id ? 'selected' : ''} onClick={() => go(id)}><Icon /><span>{label}</span></button>)}</nav>
      <button className="sidebar-chat" onClick={() => setChatOpen(true)}><MessageSquareText /><div><b>测试知识智能体</b><small>报告查询与专业问答</small></div></button>
      <button className={`system-state ${view === 'system' ? 'selected' : ''}`} onClick={() => go('system')} title="查看系统运行能力"><i className={connected ? 'online' : ''} /><div><b>{connected ? '系统在线' : '正在重连'}</b><small>语言、范围、质量与执行策略</small></div></button>
    </aside>
    <div className="workspace">
      <header className="topbar">
        <button className="menu-button" title="打开导航" onClick={() => setMenuOpen(true)}><Menu /></button>
        <ExperimentSwitcher runtime={runtime} onSelect={selectExperiment} />
        <div className={`connection ${connected ? 'online' : ''}`}>{connected ? <Wifi /> : <WifiOff />}<span>{connected ? '实时同步' : '等待状态流'}</span></div>
        <button className="top-chat" title="打开测试知识智能体" onClick={() => setChatOpen(true)}><MessageSquareText /><span>对话</span></button>
      </header>
      <main>{content}</main>
    </div>
    <ChatWorkspace open={chatOpen} runtime={runtime} onClose={() => setChatOpen(false)} />
    {detail && <DetailDrawer detail={detail} onClose={() => setDetail(null)} />}
  </div>;
}
