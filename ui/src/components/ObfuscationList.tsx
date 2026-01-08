import { ObfuscationTerm } from '../types'
import './ObfuscationList.css'

interface ObfuscationListProps {
  obfuscations: ObfuscationTerm[]
  onChange: (obfuscations: ObfuscationTerm[]) => void
}

function ObfuscationList({ obfuscations, onChange }: ObfuscationListProps) {
  const handleTextChange = (index: number, text: string) => {
    const updated = [...obfuscations]
    updated[index] = { ...updated[index], text }
    onChange(updated)
  }

  const handleReplaceChange = (index: number, replace_with: string) => {
    const updated = [...obfuscations]
    updated[index] = { ...updated[index], replace_with: replace_with || undefined }
    onChange(updated)
  }

  const handleAdd = () => {
    onChange([...obfuscations, { text: '', type: 'USER_DEFINED' }])
  }

  const handleRemove = (index: number) => {
    if (obfuscations.length > 1) {
      onChange(obfuscations.filter((_, i) => i !== index))
    } else {
      onChange([{ text: '', type: 'USER_DEFINED' }])
    }
  }

  return (
    <div className="obfuscation-list">
      {obfuscations.map((item, index) => (
        <div key={index} className="obfuscation-item">
          <input
            type="text"
            placeholder="Text to find"
            value={item.text}
            onChange={(e) => handleTextChange(index, e.target.value)}
          />
          <input
            type="text"
            placeholder="Replace with (optional)"
            value={item.replace_with || ''}
            onChange={(e) => handleReplaceChange(index, e.target.value)}
          />
          <button
            className="btn btn-danger"
            onClick={() => handleRemove(index)}
          >
            X
          </button>
        </div>
      ))}
      <button className="btn btn-add" onClick={handleAdd}>
        + Add
      </button>
    </div>
  )
}

export default ObfuscationList
