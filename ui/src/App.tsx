import { useState } from 'react';
import { Tabs, Tab } from './components/layout';
import { UserConfig } from './components/config/UserConfig';
import { AdminConfig } from './components/config/AdminConfig';
import { FileUpload, TextInput } from './components/upload';
import { ProcessingStatus } from './components/processing';
import { ResultsContainer, TextResultCard } from './components/results';
import { useUserConfig } from './hooks/useUserConfig';
import { useAdminConfig } from './hooks/useAdminConfig';
import { useFileProcessor } from './hooks/useFileProcessor';
import { useTextProcessor } from './hooks/useTextProcessor';
import './App.css';

const CONFIG_TABS: Tab[] = [
  { id: 'user', label: 'הגדרות משתמש' },
  { id: 'admin', label: 'הגדרות מנהל' },
];

const INPUT_TABS: Tab[] = [
  { id: 'pdf', label: 'קובץ PDF' },
  { id: 'text', label: 'טקסט' },
];

function App() {
  const [activeTab, setActiveTab] = useState('user');
  const [inputMode, setInputMode] = useState<'pdf' | 'text'>('pdf');

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
    processing: fileProcessing,
    addFiles,
    clearFiles,
    processAll,
  } = useFileProcessor();

  // Text processor
  const {
    text,
    result: textResult,
    processing: textProcessing,
    setText,
    clearText,
    processText,
  } = useTextProcessor();

  const processing = fileProcessing || textProcessing;

  const handleProcess = () => {
    if (inputMode === 'pdf') {
      processAll(userConfig);
    } else {
      processText(userConfig);
    }
  };

  const canProcess = inputMode === 'pdf' ? files.length > 0 : text.trim().length > 0;

  return (
    <div className="app" dir="rtl">
      <header className="header">
        <h1>סושקו - מחלץ טקסט מ-PDF</h1>
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
          <Tabs tabs={CONFIG_TABS} activeTab={activeTab} onTabChange={setActiveTab} />

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
          <h2>קלט לעיבוד</h2>
          <Tabs tabs={INPUT_TABS} activeTab={inputMode} onTabChange={(id) => setInputMode(id as 'pdf' | 'text')} />

          {inputMode === 'pdf' ? (
            <FileUpload
              files={files}
              onFilesAdd={addFiles}
              onClear={clearFiles}
              disabled={processing}
            />
          ) : (
            <TextInput
              text={text}
              onTextChange={setText}
              onClear={clearText}
              disabled={processing}
            />
          )}
        </section>

        <section className="card">
          <button
            className="btn btn-primary"
            onClick={handleProcess}
            disabled={!canProcess || processing}
          >
            {processing ? 'מעבד...' : inputMode === 'pdf'
              ? `עבד ${files.length || ''} קובץ PDF${files.length !== 1 ? 'ים' : ''}`
              : 'עבד טקסט'
            }
          </button>
        </section>

        {inputMode === 'pdf' && (
          <>
            <ProcessingStatus results={results} processing={fileProcessing} />
            <ResultsContainer results={results} />
          </>
        )}

        {inputMode === 'text' && textResult && (
          <section className="card results-section">
            <h2>תוצאות</h2>
            <TextResultCard result={textResult} />
          </section>
        )}
      </main>
    </div>
  );
}

export default App;
