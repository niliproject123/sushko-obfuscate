import { useRef, useState, DragEvent } from 'react'
import './FileUpload.css'

interface FileUploadProps {
  file: File | null
  onFileSelect: (file: File | null) => void
}

function FileUpload({ file, onFileSelect }: FileUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragOver, setDragOver] = useState(false)

  const handleClick = () => {
    inputRef.current?.click()
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      onFileSelect(files[0])
    }
  }

  const handleDragOver = (e: DragEvent) => {
    e.preventDefault()
    setDragOver(true)
  }

  const handleDragLeave = () => {
    setDragOver(false)
  }

  const handleDrop = (e: DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const files = e.dataTransfer.files
    if (files.length > 0 && files[0].type === 'application/pdf') {
      onFileSelect(files[0])
    }
  }

  return (
    <div>
      <div
        className={`upload-area ${dragOver ? 'dragover' : ''}`}
        onClick={handleClick}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <p>Drag and drop a PDF file here, or click to browse</p>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf"
          onChange={handleChange}
        />
      </div>
      {file && (
        <div className="file-info">
          Selected: {file.name} ({(file.size / 1024).toFixed(1)} KB)
        </div>
      )}
    </div>
  )
}

export default FileUpload
