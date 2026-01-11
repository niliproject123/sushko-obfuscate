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
  { id: 'user', label: 'הגדרות משתמש' },
  { id: 'admin', label: 'הגדרות מנהל' },
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
    <div className="app" dir="rtl">
      <header className="header">
        <h1>מחלץ טקסט מ-PDF</h1>
        <p>חילוץ טקסט מקבצי PDF והסתרת מידע אישי מזהה</p>
      </header>

      <main className="main">
        <section className="card info-section">
          <h2>איך זה עובד?</h2>
          <div className="info-content">
            <p>
              <strong>1. העלאת קובץ:</strong> העלה קבצי PDF שברצונך לעבד
            </p>
            <p>
              <strong>2. הגדרות אישיות (אופציונלי):</strong> ניתן להוסיף החלפות טקסט מותאמות אישית או להשבית גלאים מסוימים - המערכת תעבוד גם בלי הגדרות נוספות
            </p>
            <p>
              <strong>3. עיבוד:</strong> לחץ על "עבד" והמערכת תזהה ותחליף מידע אישי מזהה (ת.ז., טלפון, שמות, כתובות ועוד)
            </p>
            <p>
              <strong>4. הורדה:</strong> הורד את הקובץ המעובד עם המידע המוסתר
            </p>
          </div>
        </section>

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
          <h2>העלאת קבצי PDF</h2>
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
            {processing ? 'מעבד...' : `עבד ${files.length || ''} קובץ PDF${files.length !== 1 ? 'ים' : ''}`}
          </button>
        </section>

        <ProcessingStatus results={results} processing={processing} />

        <ResultsContainer results={results} />
      </main>
    </div>
  );
}

export default App;
