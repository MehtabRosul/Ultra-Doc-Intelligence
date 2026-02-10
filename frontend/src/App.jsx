import React, { useState } from 'react'
import FileUpload from './components/FileUpload'
import ChatInterface from './components/ChatInterface'
import ExtractionView from './components/ExtractionView'

export default function App() {
    const [documentId, setDocumentId] = useState(null)
    const [docInfo, setDocInfo] = useState(null)
    const [isUploading, setIsUploading] = useState(false)
    const [activeTab, setActiveTab] = useState('chat')
    const [suggestedQuestions, setSuggestedQuestions] = useState([])

    const [chatMessages, setChatMessages] = useState([])

    const handleUploadSuccess = (data) => {
        setDocumentId(data.document_id)
        setDocInfo(data)
        setSuggestedQuestions(data.suggested_questions || [])
        // Reset chat on new upload if desired, or keep history. 
        // Usually good to reset on new doc upload:
        setChatMessages([])
        setActiveTab('chat')
    }

    return (
        <div className="app">
            <div className="dashboard-container">
                {/* Header Area */}
                <header className="dashboard-header">
                    <div className="logo-section">
                        <div className="logo-icon">🔮</div>
                        <h1 className="app-title">Ultra Doc-Intelligence</h1>
                    </div>
                    <div className="header-controls">
                        <span className="version-tag">v1.0-beta</span>
                    </div>
                </header>

                {/* Bento Grid Layout */}
                <div className="bento-grid">

                    {/* Card 1: Upload Zone (Top Left) */}
                    <div className="bento-card card-upload">
                        <div className="card-header">
                            <span className="card-icon">📤</span>
                            <h3>Document Upload</h3>
                        </div>
                        <div className="card-content">
                            <FileUpload
                                onUploadSuccess={handleUploadSuccess}
                                isUploading={isUploading}
                                setIsUploading={setIsUploading}
                            />
                        </div>
                    </div>

                    {/* Card 2: Document Stats (Middle Left) */}
                    <div className="bento-card card-stats">
                        <div className="card-header">
                            <span className="card-icon">📊</span>
                            <h3>File Stats</h3>
                        </div>
                        {docInfo ? (
                            <div className="stats-grid">
                                <div className="stat-item">
                                    <label>Filename</label>
                                    <span title={docInfo.filename}>
                                        {docInfo.filename.length > 18 ? docInfo.filename.slice(0, 15) + '...' + docInfo.filename.slice(-3) : docInfo.filename}
                                    </span>
                                </div>
                                <div className="stat-item">
                                    <label>Size</label>
                                    <span>{docInfo.fileSize ? (docInfo.fileSize / 1024).toFixed(1) + ' KB' : '--'}</span>
                                </div>
                                <div className="stat-item">
                                    <label>Type</label>
                                    <span>{docInfo.fileType || 'DOC'}</span>
                                </div>
                                <div className="stat-item">
                                    <label>Time</label>
                                    <span>{docInfo.uploadTime || '--:--'}</span>
                                </div>
                                <div className="stat-item">
                                    <label>Chunks</label>
                                    <span>{docInfo.num_chunks}</span>
                                </div>
                                <div className="stat-item">
                                    <label>Security</label>
                                    <span className="status-badge encrypted">AES-256</span>
                                </div>
                            </div>
                        ) : (
                            <div className="empty-stats">
                                <p>No document loaded</p>
                            </div>
                        )}
                    </div>

                    {/* Card 3: Main Analysis (Right - Spans full height) */}
                    <div className="bento-card card-analysis">
                        <div className="card-header header-with-tabs">
                            <div className="header-left">
                                <span className="card-icon">🧠</span>
                                <h3>Analysis Engine</h3>
                            </div>
                            <div className="header-tabs">
                                <button
                                    className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
                                    onClick={() => setActiveTab('chat')}
                                >
                                    Chat
                                </button>
                                <button
                                    className={`tab-btn ${activeTab === 'extract' ? 'active' : ''}`}
                                    onClick={() => setActiveTab('extract')}
                                >
                                    Extraction
                                </button>
                            </div>
                        </div>
                        <div className="analysis-content">
                            {activeTab === 'chat' ? (
                                <ChatInterface
                                    documentId={documentId}
                                    suggestedQuestions={suggestedQuestions}
                                    messages={chatMessages}
                                    setMessages={setChatMessages}
                                />
                            ) : (
                                <ExtractionView documentId={documentId} />
                            )}
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <footer className="dashboard-footer">
                    <p>
                        AI-Powered Logistics Analysis • <span className="highlight">Ultra Doc-Intelligence</span> • Please verify all AI-generated results, as AI can make mistakes. • Built by <a href="https://mehtab-portfolio-sooty.vercel.app/" target="_blank" rel="noopener noreferrer" className="highlight" style={{ textDecoration: 'none' }}>Mehtab Rosul</a>
                    </p>
                </footer>
            </div>
        </div >
    )
}
