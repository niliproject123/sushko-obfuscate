import { useState } from 'react';
import { ReplacementEditor } from './ReplacementEditor';
import type { UserConfig as UserConfigType, PIIPatternConfig } from '../../types';
import './UserConfig.css';

// Examples for each detector pattern to help non-technical users understand
const DETECTOR_EXAMPLES: Record<string, string> = {
  israeli_id: 'לדוגמה: 123456789',
  israeli_id_short: 'לדוגמה: 1234567 או 12345678',
  phone_mobile: 'לדוגמה: 050-1234567',
  phone_landline: 'לדוגמה: 03-1234567',
  email: 'לדוגמה: user@example.com',
  hebrew_first_name: 'לדוגמה: שם פרטי: דוד',
  hebrew_last_name: 'לדוגמה: שם משפחה: כהן',
  hebrew_full_name: 'לדוגמה: שם מלא: דוד כהן',
  hebrew_father_name: 'לדוגמה: שם האב: אברהם',
  english_first_name: 'לדוגמה: Name: David',
  english_last_name: 'לדוגמה: Last Name: Cohen',
  city: 'לדוגמה: ישוב: תל אביב',
  street: 'לדוגמה: רחוב: הרצל',
  medical_license: 'לדוגמה: מ.ר. 12345',
  case_number: 'לדוגמה: מקרה מספר: 12345',
  bank_account: 'לדוגמה: מספר חשבון בנק: 123456',
  bank_branch: 'לדוגמה: קוד סניף: 123',
  doctor_name: 'לדוגמה: ד"ר ישראל ישראלי',
};

// Hebrew translations for PII types
const PII_TYPE_HEBREW: Record<string, string> = {
  ID: 'תעודת זהות',
  PHONE: 'טלפון',
  EMAIL: 'אימייל',
  NAME: 'שם',
  ADDRESS: 'כתובת',
  LICENSE: 'רישיון',
  CASE_NUMBER: 'מספר תיק',
  BANK_ACCOUNT: 'חשבון בנק',
  BANK_BRANCH: 'סניף בנק',
};

interface UserConfigProps {
  config: UserConfigType;
  onReplacementsChange: (replacements: Record<string, string>) => void;
  onToggleDetector: (name: string, disabled: boolean) => void;
  onForceOcrChange: (forceOcr: boolean) => void;
  availablePatterns?: PIIPatternConfig[];
}

export function UserConfig({
  config,
  onReplacementsChange,
  onToggleDetector,
  onForceOcrChange,
  availablePatterns = [],
}: UserConfigProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);

  return (
    <div className="user-config">
      <ReplacementEditor
        replacements={config.replacements}
        onChange={onReplacementsChange}
        title="ההחלפות שלי"
        description="הוסף טקסט לחיפוש והחלפה. אלה יקבלו עדיפות על הגדרות השרת."
        collapsible={true}
        defaultCollapsed={Object.keys(config.replacements).length === 0}
      />

      <div className="advanced-section">
        <button
          type="button"
          className="advanced-toggle"
          onClick={() => setShowAdvanced(!showAdvanced)}
        >
          {showAdvanced ? '▼' : '▶'} אפשרויות מתקדמות
        </button>

        {showAdvanced && (
          <div className="advanced-content">
            <div className="option-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={config.force_ocr}
                  onChange={(e) => onForceOcrChange(e.target.checked)}
                />
                כפה עיבוד OCR
              </label>
              <p className="option-hint">
                השתמש ב-OCR גם אם ל-PDF יש שכבת טקסט
              </p>
            </div>

            {availablePatterns.length > 0 && (
              <div className="option-group">
                <h4>השבת גלאים</h4>
                <p className="option-hint">
                  בטל סימון בדפוסים שאינך רוצה לזהות
                </p>
                <div className="detector-list">
                  {availablePatterns.map((pattern) => (
                    <div key={pattern.name} className="detector-item">
                      <label className="checkbox-label">
                        <input
                          type="checkbox"
                          checked={!config.disabled_detectors.includes(pattern.name)}
                          onChange={(e) =>
                            onToggleDetector(pattern.name, !e.target.checked)
                          }
                        />
                        <span className="detector-name">{pattern.name}</span>
                        <span className="detector-type">
                          ({PII_TYPE_HEBREW[pattern.pii_type] || pattern.pii_type})
                        </span>
                      </label>
                      {DETECTOR_EXAMPLES[pattern.name] && (
                        <p className="detector-example">
                          {DETECTOR_EXAMPLES[pattern.name]}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
