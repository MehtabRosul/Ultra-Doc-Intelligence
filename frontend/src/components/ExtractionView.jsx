import React, { useState } from 'react'
import ConfidenceBadge from './ConfidenceBadge'

const FIELD_LABELS = {
    shipment_id: 'Shipment ID',
    shipper: 'Shipper',
    consignee: 'Consignee',
    pickup_datetime: 'Pickup Date/Time',
    delivery_datetime: 'Delivery Date/Time',
    equipment_type: 'Equipment Type',
    mode: 'Mode',
    rate: 'Rate',
    currency: 'Currency',
    weight: 'Weight',
    carrier_name: 'Carrier Name',
}

export default function ExtractionView({ documentId }) {
    const [data, setData] = useState(null)
    const [confidence, setConfidence] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    const handleExtract = async () => {
        if (!documentId || loading) return
        setLoading(true)
        setError('')

        try {
            const res = await fetch('/api/extract', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ document_id: documentId }),
            })

            if (!res.ok) {
                const err = await res.json()
                throw new Error(err.detail || 'Extraction failed')
            }

            const result = await res.json()
            setData(result.data)
            setConfidence(result.confidence)
        } catch (err) {
            setError(err.message || 'Extraction failed')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="extraction">
            <button
                className={`btn btn--secondary btn--full ${loading ? 'btn--loading' : ''}`}
                onClick={handleExtract}
                disabled={!documentId || loading}
            >
                {loading ? 'Extracting...' : '🔍 Extract Structured Data'}
            </button>

            {error && (
                <div className="status-bar" style={{ borderColor: 'var(--danger)' }}>
                    <span>❌</span>
                    <span style={{ color: 'var(--danger)' }}>{error}</span>
                </div>
            )}

            {data && (
                <>
                    {confidence !== null && (
                        <div style={{ marginBottom: '16px' }}>
                            <ConfidenceBadge confidence={confidence} guardrailStatus="grounded" />
                        </div>
                    )}

                    <div className="extraction-grid">
                        {Object.entries(FIELD_LABELS).map(([key, label]) => (
                            <div key={key} className="extraction-card">
                                <div className="extraction-card__header">
                                    <span className="extraction-card__icon">{getIcon(key)}</span>
                                    <span className="extraction-card__label">{label}</span>
                                </div>
                                <div className="extraction-card__value">
                                    {data[key] !== null && data[key] !== undefined ? (
                                        data[key]
                                    ) : (
                                        <span className="extraction__null">null</span>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>

                    <button
                        className="btn btn--secondary btn--full"
                        style={{ marginTop: '16px' }}
                        onClick={() => {
                            const json = JSON.stringify(data, null, 2)
                            navigator.clipboard.writeText(json)
                        }}
                    >
                        📋 Copy JSON
                    </button>
                </>
            )}
        </div>
    )
}

const getIcon = (key) => {
    const icons = {
        shipment_id: '📦',
        shipper: '🏭',
        consignee: '📍',
        pickup_datetime: '📅',
        delivery_datetime: '🚚',
        equipment_type: '🚛',
        mode: '🛣️',
        rate: '💲',
        currency: '💱',
        weight: '⚖️',
        carrier_name: '🏢',
    }
    return icons[key] || '📄'
}
