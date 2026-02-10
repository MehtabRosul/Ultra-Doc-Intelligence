import React, { useRef, useState } from 'react'
import { API_BASE_URL } from '../config'

export default function FileUpload({ onUploadSuccess, isUploading, setIsUploading }) {
    const fileInputRef = useRef(null)
    const [dragActive, setDragActive] = useState(false)
    const [error, setError] = useState('')

    const handleFile = async (file) => {
        if (!file) return

        const ext = file.name.split('.').pop().toLowerCase()
        if (!['pdf', 'docx', 'txt'].includes(ext)) {
            setError('Unsupported file type. Please upload PDF, DOCX, or TXT.')
            return
        }

        setError('')
        setIsUploading(true)

        try {
            const formData = new FormData()
            formData.append('file', file)

            const res = await fetch(`${API_BASE_URL}/api/upload`, {
                method: 'POST',
                body: formData,
            })

            if (!res.ok) {
                const data = await res.json()
                throw new Error(data.detail || 'Upload failed')
            }

            const data = await res.json()
            // Pass backend data + client-side file metadata
            onUploadSuccess({
                ...data,
                fileSize: file.size,
                fileType: file.name.split('.').pop().toUpperCase(),
                uploadTime: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            })
        } catch (err) {
            setError(err.message || 'Upload failed. Please try again.')
        } finally {
            setIsUploading(false)
        }
    }

    const handleDrop = (e) => {
        e.preventDefault()
        setDragActive(false)
        const file = e.dataTransfer.files[0]
        handleFile(file)
    }

    const handleDrag = (e) => {
        e.preventDefault()
        setDragActive(e.type === 'dragenter' || e.type === 'dragover')
    }

    return (
        <div>
            <div
                className={`upload-zone ${dragActive ? 'upload-zone--active' : ''}`}
                onClick={() => fileInputRef.current?.click()}
                onDrop={handleDrop}
                onDragEnter={handleDrag}
                onDragOver={handleDrag}
                onDragLeave={handleDrag}
            >
                <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf,.docx,.txt"
                    style={{ display: 'none' }}
                    onChange={(e) => handleFile(e.target.files[0])}
                />

                {isUploading ? (
                    <>
                        <span className="upload-zone__icon">⏳</span>
                        <p className="upload-zone__text">Processing document...</p>
                        <div className="loading-dots">
                            <span></span><span></span><span></span>
                        </div>
                    </>
                ) : (
                    <>
                        <span className="upload-zone__icon">📄</span>
                        <p className="upload-zone__text">
                            Drop your document here or <strong>click to browse</strong>
                        </p>
                        <p className="upload-zone__hint">Supports PDF, DOCX, TXT</p>
                    </>
                )}
            </div>

            {error && (
                <div className="status-bar" style={{ marginTop: 12, borderColor: 'var(--danger)' }}>
                    <span>❌</span>
                    <span style={{ color: 'var(--danger)' }}>{error}</span>
                </div>
            )}
        </div>
    )
}
