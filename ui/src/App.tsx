import { useState } from 'react'
import FileUpload from './components/FileUpload'
import ObfuscationList from './components/ObfuscationList'
import Results from './components/Results'
import { ExtractResponse, ObfuscationTerm } from './types'
import './App.css'

function App() {
  const [file, setFile] = useState<File | null>(null)
  const [obfuscations, setObfuscations] = useState<ObfuscationTerm[]>([
    { text: '', type: 'USER_DEFINED' }
  ])
  const [results, setResults] = useState<ExtractResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleProcess = async () => {
    if (!file) return

    setLoading(true)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)

    const validObfuscations = obfuscations.filter(o => o.text.trim())
    formData.append('obfuscations', JSON.stringify(validObfuscations))

    try {
      const response = await fetch('/api/extract', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || 'Processing failed')
      }

      const data: ExtractResponse = await response.json()
      setResults(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = () => {
    if (results?.file_id) {
      window.location.href = `/api/download/${results.file_id}`
    }
  }

  return (
    <div className="app">
      <header className="header">
        <h1>PDF Text Extractor</h1>
        <p>Extract and obfuscate PII from PDF documents</p>
      </header>

      <main className="main">
        <section className="card">
          <h2>1. Upload PDF</h2>
          <FileUpload file={file} onFileSelect={setFile} />
        </section>

        <section className="card">
          <h2>2. Custom Obfuscations (Optional)</h2>
          <p className="hint">
            Add specific text to find and replace. Leave "Replace with" empty to use default placeholder.
          </p>
          <ObfuscationList
            obfuscations={obfuscations}
            onChange={setObfuscations}
          />
        </section>

        <section className="card">
          <h2>3. Process</h2>
          <button
            className="btn btn-primary"
            onClick={handleProcess}
            disabled={!file || loading}
          >
            {loading ? 'Processing...' : 'Process PDF'}
          </button>
          {error && <p className="error">{error}</p>}
        </section>

        {loading && (
          <section className="card loading">
            <div className="spinner" />
            <p>Processing your PDF...</p>
          </section>
        )}

        {results && !loading && (
          <section className="card">
            <h2>Results</h2>
            <Results results={results} />
            <button className="btn btn-primary" onClick={handleDownload}>
              Download Processed PDF
            </button>
          </section>
        )}
      </main>
    </div>
  )
}

export default App
