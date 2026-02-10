import React from 'react'

export default function ConfidenceBadge({ confidence, guardrailStatus }) {
    const percentage = Math.round(confidence * 100)

    let level = 'low'
    if (confidence >= 0.7) level = 'high'
    else if (confidence >= 0.45) level = 'medium'

    const statusLabels = {
        grounded: '✓ Grounded',
        low_confidence: '⚠ Low Confidence',
        no_context: '✕ No Context',
        refused: '✕ Refused',
    }

    return (
        <div className="message__meta">
            <span className={`confidence confidence--${level}`}>
                {level === 'high' ? '●' : level === 'medium' ? '◐' : '○'}{' '}
                {percentage}% confidence
            </span>
            {guardrailStatus && (
                <span className={`guardrail-badge guardrail-badge--${guardrailStatus}`}>
                    {statusLabels[guardrailStatus] || guardrailStatus}
                </span>
            )}
        </div>
    )
}
