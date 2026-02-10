import React, { useState, useRef, useEffect } from 'react'
import ConfidenceBadge from './ConfidenceBadge'
import { API_BASE_URL } from '../config'

export default function ChatInterface({ documentId, suggestedQuestions = [], messages, setMessages }) {
    // const [messages, setMessages] = useState([]) // Lifted to App.jsx
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const [isSidebarOpen, setIsSidebarOpen] = useState(true)
    const messagesEndRef = useRef(null)


    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])



    const submitQuestion = async (questionText) => {
        if (!questionText || loading) return

        setMessages((prev) => [...prev, { role: 'user', text: questionText }])
        setInput('')
        setLoading(true)

        try {
            const res = await fetch(`${API_BASE_URL}/api/ask`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ document_id: documentId, question: questionText }),
            })

            if (!res.ok) {
                const err = await res.json()
                throw new Error(err.detail || 'Failed to get answer')
            }

            const data = await res.json()
            setMessages((prev) => [
                ...prev,
                {
                    role: 'ai',
                    text: data.answer,
                    confidence: data.confidence,
                    guardrailStatus: data.guardrail_status,
                    sources: data.sources,
                },
            ])
        } catch (err) {
            setMessages((prev) => [
                ...prev,
                { role: 'ai', text: `Error: ${err.message}`, confidence: 0, guardrailStatus: 'refused' },
            ])
        } finally {
            setLoading(false)
        }
    }

    const handleAsk = () => {
        submitQuestion(input.trim())
    }

    const handleSuggestedClick = (question) => {
        submitQuestion(question)
    }

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            handleAsk()
        }
    }

    return (
        <div className="chat-layout">
            {/* Sidebar - Collapsible */}
            <div className={`chat-sidebar ${isSidebarOpen ? 'open' : 'closed'}`}>
                <div className="sidebar-header">
                    <h3>Insights</h3>
                    <button
                        className="sidebar-toggle-btn"
                        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                        title={isSidebarOpen ? "Close Sidebar" : "Open Sidebar"}
                    >
                        {isSidebarOpen ? '◀' : '▶'}
                    </button>
                </div>

                <div className="sidebar-content">
                    {suggestedQuestions.length > 0 ? (
                        <div className="sidebar-suggestions">
                            <h4>Suggested Queries</h4>
                            {suggestedQuestions.map((q, i) => (
                                <button
                                    key={i}
                                    className="sidebar-suggestion-item"
                                    onClick={() => handleSuggestedClick(q)}
                                >
                                    <span className="suggestion-icon">✨</span>
                                    <span className="suggestion-text">{q}</span>
                                </button>
                            ))}
                        </div>
                    ) : (
                        <div className="sidebar-empty">
                            <small>No suggestions available</small>
                        </div>
                    )}
                </div>
            </div>

            {/* Main Chat Area */}
            <div className="qa-dashboard">
                {!isSidebarOpen && (
                    <button
                        className="sidebar-open-tab"
                        onClick={() => setIsSidebarOpen(true)}
                    >
                        💡
                    </button>
                )}

                {/* Q&A Feed (Result Cards) */}
                <div className="qa-feed">
                    {messages.length === 0 && (
                        <div className="qa-empty-state">
                            <div className="qa-empty-icon">🔮</div>
                            <h3>Ready to analyze</h3>
                            <p>Select a question from the sidebar or type your own below.</p>
                        </div>
                    )}

                    {messages.map((msg, i) => {
                        // We only want to render "AI" responses as cards, 
                        // combining the preceding "User" question into the card title if possible.
                        // But our state is [User, AI, User, AI].
                        // Let's render pairs. Simple way: Render User msg as Title, AI msg as Body.
                        // But sometimes we might have just User msg (loading).

                        if (msg.role === 'user') {
                            // Check if next message is AI
                            const nextMsg = messages[i + 1]
                            const isLoading = loading && i === messages.length - 1

                            // If next is AI, let the AI iteration handle it? 
                            // Or render a card for every User message and fill the body?
                            // Let's render a card for the User Question.
                            return (
                                <div key={i} className="qa-card">
                                    <div className="qa-card__header">
                                        <h3 className="qa-card__title">{msg.text}</h3>
                                    </div>
                                    <div className="qa-card__body">
                                        {nextMsg && nextMsg.role === 'ai' ? (
                                            <>
                                                <div className="qa-answer-text">{nextMsg.text}</div>
                                                {nextMsg.confidence !== undefined && (
                                                    <div className="qa-card__footer">
                                                        <ConfidenceBadge
                                                            confidence={nextMsg.confidence}
                                                            guardrailStatus={nextMsg.guardrailStatus}
                                                        />
                                                        {nextMsg.sources && nextMsg.sources.length > 0 && (
                                                            <SourcesPanel sources={nextMsg.sources} />
                                                        )}
                                                    </div>
                                                )}
                                            </>
                                        ) : isLoading ? (
                                            <div className="loading-dots">
                                                <span></span><span></span><span></span>
                                            </div>
                                        ) : null}
                                    </div>
                                </div>
                            )
                        }
                        return null // Skip AI messages as they are handled by the User message iteration
                    })}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input Area */}
                <div className="qa-input-area">
                    <input
                        className="qa-input"
                        type="text"
                        placeholder="Ask a specific question about the document..."
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        disabled={!documentId || loading}
                    />
                    <button
                        className="btn btn--primary qa-send-btn"
                        onClick={handleAsk}
                        disabled={!documentId || !input.trim() || loading}
                    >
                        ➔
                    </button>
                </div>
            </div>
        </div>
    )
}

function SourcesPanel({ sources }) {
    const [open, setOpen] = useState(false)

    return (
        <div className="sources">
            <button className="sources__toggle" onClick={() => setOpen(!open)}>
                {open ? '▾' : '▸'} {sources.length} source{sources.length !== 1 ? 's' : ''}
            </button>
            {open && (
                <div className="sources__list">
                    {sources.map((src, i) => (
                        <div key={i} className="source-chip">
                            <span className="source-chip__score">
                                Relevance: {Math.round(src.similarity_score * 100)}%
                            </span>
                            <p>{src.text.length > 300 ? src.text.slice(0, 300) + '...' : src.text}</p>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}
