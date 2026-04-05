import { useState, useEffect, useRef, useCallback } from 'react';
import { getParticipants, getParticipant, saveParticipant, deleteParticipant, downloadUrl } from './api';
import './App.css';

const FREQ_OPTIONS = ['', 'Per day', 'Per week', 'Per Month', 'Never'];

// ── Section header labels ──────────────────────────────────────────────────
const SECTION_LABELS = {
  '1': 'STAPLE FOOD / CEREALS',
  '2': 'VEGETABLES',
  '3': 'POTATOES & PRODUCTS',
  '4': 'FRUITS',
  '5': 'MILK, DAIRY & ALTERNATIVES',
  '6': 'MEAT',
  '7': 'FISH AND SEAFOOD',
  '8': 'NUTS, PULSES AND SEEDS',
  '9': 'TRADITIONAL MIXED DISHES',
  '10': 'ARABIC SWEETS',
  '11': 'DESSERTS & PASTRIES',
  '12': 'BEVERAGES',
  '13': 'HONEY, JAM & ADDED SUGAR',
  '15': 'FATS & OILS (ON BREADS)',
  '16': 'FATS & OILS (COOKING)',
  '17': 'CONDIMENTS',
};

function completionPct(rows) {
  if (!rows.length) return 0;
  const answered = rows.filter(r => r.frequency && r.frequency.trim() !== '').length;
  return answered / rows.length;
}

// ── Sidebar ────────────────────────────────────────────────────────────────
function Sidebar({ participants, activeUid, onLoad, onDelete, saveStatus }) {
  const [newId, setNewId] = useState('');
  const [confirmDelete, setConfirmDelete] = useState(null);

  const handleCreate = async () => {
    const uid = newId.trim();
    if (!uid) return;
    setNewId('');
    await onLoad(uid);
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <span className="brand-icon">🥗</span>
        <div>
          <div className="brand-title">FFQ Manager</div>
          <div className="brand-sub">Food Frequency Questionnaire</div>
        </div>
      </div>

      <div className="sidebar-section">
        <label className="sidebar-label">New Participant</label>
        <div className="input-row">
          <input
            className="text-input"
            placeholder="e.g. P001"
            value={newId}
            onChange={e => setNewId(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleCreate()}
          />
          <button className="btn-create" onClick={handleCreate} title="Create participant">＋</button>
        </div>
      </div>

      <div className="sidebar-section">
        <label className="sidebar-label">Participants ({participants.length})</label>
        <div className="participant-list">
          {participants.length === 0 && (
            <div className="empty-list">No participants yet</div>
          )}
          {participants.map(uid => (
            <div
              key={uid}
              className={`participant-item ${uid === activeUid ? 'active' : ''}`}
            >
              <button className="participant-btn" onClick={() => onLoad(uid)}>
                <span className="p-id mono">{uid}</span>
              </button>
              {confirmDelete === uid ? (
                <div className="confirm-del">
                  <button className="del-yes" onClick={() => { onDelete(uid); setConfirmDelete(null); }}>✓</button>
                  <button className="del-no" onClick={() => setConfirmDelete(null)}>✕</button>
                </div>
              ) : (
                <button className="del-btn" onClick={() => setConfirmDelete(uid)} title="Delete">🗑</button>
              )}
            </div>
          ))}
        </div>
      </div>

      {saveStatus && (
        <div className={`save-status ${saveStatus.type}`}>
          {saveStatus.type === 'saving' && <span className="pulse-dot" />}
          {saveStatus.type === 'saved' && '✓ '}
          {saveStatus.type === 'error' && '⚠ '}
          {saveStatus.msg}
        </div>
      )}
    </aside>
  );
}

// ── Progress Bar ──────────────────────────────────────────────────────────
function ProgressBar({ pct }) {
  return (
    <div className="progress-wrap">
      <div className="progress-track">
        <div className="progress-fill" style={{ width: `${Math.round(pct * 100)}%` }} />
      </div>
      <span className="progress-label">{Math.round(pct * 100)}% complete</span>
    </div>
  );
}

// ── Section Nav ───────────────────────────────────────────────────────────
function SectionNav({ sections, activeSection, onSelect }) {
  return (
    <nav className="section-nav">
      {sections.map(sec => (
        <button
          key={sec}
          className={`sec-btn ${sec === activeSection ? 'active' : ''}`}
          onClick={() => onSelect(sec)}
        >
          <span className="sec-num">{sec}</span>
          <span className="sec-name">{SECTION_LABELS[sec] || sec}</span>
        </button>
      ))}
    </nav>
  );
}

// ── Food Table ────────────────────────────────────────────────────────────
function FoodTable({ rows, onUpdate }) {
  function handleChange(idx, field, value) {
    onUpdate(idx, field, value);
  }

  return (
    <div className="table-wrap">
      <table className="food-table">
        <thead>
          <tr>
            <th className="col-id">ID</th>
            <th className="col-name">Food Item</th>
            <th className="col-poption">Portion Option</th>
            <th className="col-psize">Portion Size</th>
            <th className="col-freq">Frequency</th>
            <th className="col-fcount">Count</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => (
            <tr
              key={row.id}
              className={`food-row ${row.frequency ? 'answered' : ''}`}
            >
              <td className="col-id mono">{row.id}</td>
              <td className="col-name">{row.name}</td>
              <td className="col-poption">
                <select
                  className="cell-select"
                  value={row.selected_portion_option}
                  onChange={e => handleChange(idx, 'selected_portion_option', e.target.value)}
                >
                  {row.portion_options.map(o => <option key={o} value={o}>{o || '—'}</option>)}
                </select>
              </td>
              <td className="col-psize">
                <input
                  type="number"
                  className="cell-number"
                  min={0}
                  value={row.portion_size || ''}
                  onChange={e => handleChange(idx, 'portion_size', parseFloat(e.target.value) || 0)}
                />
              </td>
              <td className="col-freq">
                <select
                  className={`cell-select freq-select ${row.frequency === 'Never' ? 'never' : row.frequency ? 'has-val' : ''}`}
                  value={row.frequency}
                  onChange={e => handleChange(idx, 'frequency', e.target.value)}
                >
                  {FREQ_OPTIONS.map(o => <option key={o} value={o}>{o || '—'}</option>)}
                </select>
              </td>
              <td className="col-fcount">
                <input
                  type="number"
                  className="cell-number"
                  min={0}
                  value={row.frequency_count || ''}
                  disabled={row.frequency === 'Never' || !row.frequency}
                  onChange={e => handleChange(idx, 'frequency_count', parseFloat(e.target.value) || 0)}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── Main App ──────────────────────────────────────────────────────────────
export default function App() {
  const [participants, setParticipants] = useState([]);
  const [activeUid, setActiveUid] = useState(null);
  const [allRows, setAllRows] = useState([]);
  const [activeSection, setActiveSection] = useState(null);
  const [saveStatus, setSaveStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const dirtyRef = useRef(false);
  const autoSaveRef = useRef(null);

  // Load participant list on mount
  useEffect(() => {
    getParticipants().then(setParticipants).catch(() => {});
  }, []);

  // Sections derived from rows
  const sections = [...new Set(allRows.map(r => r.section))];
  const visibleRows = activeSection
    ? allRows.filter(r => r.section === activeSection)
    : allRows;

  // Auto-save every 2 minutes
  useEffect(() => {
    if (autoSaveRef.current) clearInterval(autoSaveRef.current);
    if (!activeUid) return;

    autoSaveRef.current = setInterval(() => {
      if (dirtyRef.current) {
        triggerSave(activeUid, allRows, 'auto');
      }
    }, 2 * 60 * 1000);

    return () => clearInterval(autoSaveRef.current);
  }, [activeUid, allRows]);

  const triggerSave = useCallback(async (uid, rows, mode = 'manual') => {
    if (!uid) return;
    setSaveStatus({ type: 'saving', msg: mode === 'auto' ? 'Auto-saving…' : 'Saving…' });
    try {
      await saveParticipant(uid, rows);
      dirtyRef.current = false;
      setSaveStatus({ type: 'saved', msg: mode === 'auto' ? 'Auto-saved' : 'Saved!' });
      setTimeout(() => setSaveStatus(null), 3000);
    } catch {
      setSaveStatus({ type: 'error', msg: 'Save failed' });
    }
  }, []);

  const handleDownload = useCallback(async () => {
    await triggerSave(activeUid, allRows, 'manual');
    window.location.href = downloadUrl(activeUid);
  }, [activeUid, allRows, triggerSave]);

  async function loadParticipant(uid) {
    setLoading(true);
    try {
      const data = await getParticipant(uid);
      console.log(data)
      setActiveUid(uid);
      setAllRows(data.rows);
      setActiveSection(null);
      dirtyRef.current = false;
      // refresh list
      const list = await getParticipants();
      setParticipants(list);
    } catch {
      setSaveStatus({ type: 'error', msg: 'Failed to load participant' });
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(uid) {
    await deleteParticipant(uid);
    if (uid === activeUid) {
      setActiveUid(null);
      setAllRows([]);
    }
    setParticipants(p => p.filter(x => x !== uid));
  }

  function handleUpdate(visibleIdx, field, value) {
    // Map visible index back to allRows index
    const rowId = visibleRows[visibleIdx].id;
    setAllRows(prev => {
      const next = prev.map(r => r.id === rowId ? { ...r, [field]: value } : r);
      dirtyRef.current = true;
      return next;
    });
  }

  const pct = completionPct(allRows);

  return (
    <div className="layout">
      <Sidebar
        participants={participants}
        activeUid={activeUid}
        onLoad={loadParticipant}
        onDelete={handleDelete}
        saveStatus={saveStatus}
      />

      <main className="main">
        {!activeUid ? (
          <div className="welcome">
            <div className="welcome-icon">🥗</div>
            <h1 className="welcome-title">Food Frequency Questionnaire</h1>
            <p className="welcome-sub">Create or load a participant from the sidebar to begin.</p>
          </div>
        ) : (
          <>
            <header className="main-header">
              <div className="header-left">
                <h1 className="page-title">Food Frequency Questionnaire</h1>
                <span className="participant-badge mono">{activeUid}</span>
              </div>
              <div className="header-right">
                <button
                  className="btn-save"
                  onClick={() => triggerSave(activeUid, allRows, 'manual')}
                  disabled={saveStatus?.type === 'saving'}
                >
                  💾 Save
                </button>
                <button
                  className="btn-download"
                  onClick={handleDownload}
                  disabled={saveStatus?.type === 'saving'}
                >
                  ⬇ Download CSV
                </button>
              </div>
            </header>

            <ProgressBar pct={pct} />

            <div className="content-body">
              <SectionNav
                sections={sections}
                activeSection={activeSection}
                onSelect={s => setActiveSection(prev => prev === s ? null : s)}
              />

              {loading ? (
                <div className="loading-msg">Loading…</div>
              ) : (
                <FoodTable
                  rows={visibleRows}
                  onUpdate={handleUpdate}
                />
              )}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
