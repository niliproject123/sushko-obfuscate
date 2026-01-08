import React, { useRef, useState, DragEvent } from 'react';
import './FileUpload.css';

interface FileUploadProps {
  files: File[];
  onFilesAdd: (files: FileList | File[]) => void;
  onClear: () => void;
  disabled?: boolean;
}

export function FileUpload({ files, onFilesAdd, onClear, disabled = false }: FileUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  const handleClick = () => {
    if (!disabled) {
      inputRef.current?.click();
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = e.target.files;
    if (selectedFiles && selectedFiles.length > 0) {
      onFilesAdd(selectedFiles);
    }
    // Reset input so same file can be selected again
    if (inputRef.current) {
      inputRef.current.value = '';
    }
  };

  const handleDragOver = (e: DragEvent) => {
    e.preventDefault();
    if (!disabled) {
      setDragOver(true);
    }
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (disabled) return;

    const droppedFiles = Array.from(e.dataTransfer.files).filter(
      (f) => f.type === 'application/pdf'
    );
    if (droppedFiles.length > 0) {
      onFilesAdd(droppedFiles);
    }
  };

  const formatSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="file-upload">
      <div
        className={`upload-area ${dragOver ? 'dragover' : ''} ${disabled ? 'disabled' : ''}`}
        onClick={handleClick}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className="upload-icon">📄</div>
        <p className="upload-text">
          Drag and drop PDF files here, or click to browse
        </p>
        <p className="upload-hint">Multiple files supported</p>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf"
          multiple
          onChange={handleChange}
          disabled={disabled}
        />
      </div>

      {files.length > 0 && (
        <div className="file-list">
          <div className="file-list-header">
            <span>{files.length} file{files.length !== 1 ? 's' : ''} selected</span>
            <button type="button" onClick={onClear} className="clear-btn">
              Clear All
            </button>
          </div>
          <ul>
            {files.map((file, index) => (
              <li key={`${file.name}-${index}`}>
                <span className="file-name">{file.name}</span>
                <span className="file-size">{formatSize(file.size)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
