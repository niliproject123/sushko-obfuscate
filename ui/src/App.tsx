import { useState } from 'react';
import { Tabs, Tab } from './components/layout';
import { UserConfig } from './components/config/UserConfig';
import { AdminConfig } from './components/config/AdminConfig';
import { FileUpload } from './components/upload';
import { ProcessingStatus } from './components/processing';
import { ResultsContainer } from './components/results';
import { useUserConfig } from './hooks/useUserConfig';
import { useAdminConfig } from './hooks/useAdminConfig';
import { useFileProcessor } from './hooks/useFileProcessor';
import './App.css';

const TABS: Tab[] = [
  { id: 'user', label: 'User Config' },
  { id: 'admin', label: 'Admin Config' },
];

function App() {
  const [activeTab, setActiveTab] = useState('user');

  // User config (localStorage)
  const {
    config: userConfig,
    setReplacements,
    toggleDetector,
    setForceOcr,
  } = useUserConfig();

  // Admin config (server)
  const {
    config: adminConfig,
    loading: adminLoading,
    error: adminError,
    refresh: refreshAdminConfig,
    addPattern,
    updatePattern,
    deletePattern,
    updatePool,
    updateOcr,
    updatePlaceholders,
    updateDefaultReplacements,
  } = useAdminConfig();

  // File processor
  const {
    files,
    results,
    processing,
    addFiles,
    clearFiles,
    processAll,
  } = useFileProcessor();

  const handleProcess = () => {
    processAll(userConfig);
  };

  return (
    <div className="app">
      <header className="header">
        <h1>PDF Text Extractor</h1>
        <p>Extract and obfuscate PII from PDF documents</p>
      </header>

      <main className="main">
        <section className="card">
          <Tabs tabs={TABS} activeTab={activeTab} onTabChange={setActiveTab} />

          {activeTab === 'user' && (
            <UserConfig
              config={userConfig}
              onReplacementsChange={setReplacements}
              onToggleDetector={toggleDetector}
              onForceOcrChange={setForceOcr}
              availablePatterns={adminConfig?.patterns}
            />
          )}

          {activeTab === 'admin' && (
            <AdminConfig
              config={adminConfig}
              loading={adminLoading}
              error={adminError}
              onRefresh={refreshAdminConfig}
              onAddPattern={addPattern}
              onUpdatePattern={updatePattern}
              onDeletePattern={deletePattern}
              onUpdatePool={updatePool}
              onUpdateOcr={updateOcr}
              onUpdatePlaceholders={updatePlaceholders}
              onUpdateDefaultReplacements={updateDefaultReplacements}
            />
          )}
        </section>

        <section className="card">
          <h2>Upload PDFs</h2>
          <FileUpload
            files={files}
            onFilesAdd={addFiles}
            onClear={clearFiles}
            disabled={processing}
          />
        </section>

        <section className="card">
          <button
            className="btn btn-primary"
            onClick={handleProcess}
            disabled={files.length === 0 || processing}
          >
            {processing ? 'Processing...' : `Process ${files.length || ''} PDF${files.length !== 1 ? 's' : ''}`}
          </button>
        </section>

        <ProcessingStatus results={results} processing={processing} />

        <ResultsContainer results={results} />
      </main>
    </div>
  );
}

export default App;
