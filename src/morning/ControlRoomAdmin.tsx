import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { morningApi } from './api'

type Observation = {
  id: string
  reporting_date: string
  machine_id: string | null
  raw_machine_label: string
  start_time: string | null
  end_time: string | null
  description: string
  source_message_id: string
}

function localDate(): string {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function timePart(value: string | null): string {
  return value ? value.slice(11, 16) : '—'
}

export function ControlRoomAdmin() {
  const queryClient = useQueryClient()
  const [reportingDate, setReportingDate] = useState(localDate)
  const [text, setText] = useState('')
  const [pdfBase64, setPdfBase64] = useState<string | null>(null)
  const [fileName, setFileName] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const observations = useQuery({
    queryKey: ['control-room-observations', reportingDate],
    queryFn: () => morningApi<{ observations: Observation[] }>(
      `/api/morning/admin/control-room/observations?reporting_date=${reportingDate}`,
    ),
  })

  const ingest = useMutation({
    mutationFn: () => morningApi<{ observations: Observation[] }>('/api/morning/admin/control-room/ingest', {
      method: 'POST',
      body: JSON.stringify({
        reporting_date: reportingDate,
        text: text.trim() || null,
        pdf_base64: text.trim() ? null : pdfBase64,
      }),
    }),
    onSuccess: (result) => {
      setMessage(`${result.observations.length} control-room observation(s) imported.`)
      setText('')
      setPdfBase64(null)
      setFileName(null)
      void queryClient.invalidateQueries({ queryKey: ['control-room-observations', reportingDate] })
    },
  })

  const choosePdf = (file: File | null) => {
    setMessage(null)
    if (!file) {
      setPdfBase64(null)
      setFileName(null)
      return
    }
    const reader = new FileReader()
    reader.onload = () => {
      const result = String(reader.result || '')
      setPdfBase64(result.includes(',') ? result.split(',', 2)[1] : result)
      setFileName(file.name)
    }
    reader.readAsDataURL(file)
  }

  return (
    <section className="morning-admin-card morning-control-room-card">
      <h3>Control-room input</h3>
      <p className="meta">
        Import the production-delay report for the selected reporting date. Only machines explicitly placed in
        control-room scope are extracted; the source cannot expand that scope by itself.
      </p>

      <div className="morning-control-room-grid">
        <div className="morning-add-form">
          <label>
            Reporting date
            <input type="date" value={reportingDate} onChange={(event) => setReportingDate(event.target.value)} />
          </label>
          <label>
            PDF report
            <input type="file" accept="application/pdf,.pdf" onChange={(event) => choosePdf(event.target.files?.[0] || null)} />
          </label>
          {fileName ? <div className="meta">Selected: {fileName}</div> : null}
          <div className="meta">or paste the PDF text layer below</div>
          <textarea
            placeholder="Paste control-room Production Delays text"
            value={text}
            onChange={(event) => setText(event.target.value)}
          />
          {ingest.isError ? <p className="error-text">{ingest.error instanceof Error ? ingest.error.message : 'Import failed.'}</p> : null}
          {message ? <p className="morning-status-ok">{message}</p> : null}
          <button
            type="button"
            className="primary"
            disabled={ingest.isPending || (!text.trim() && !pdfBase64)}
            onClick={() => ingest.mutate()}
          >
            {ingest.isPending ? 'Importing…' : 'Import control-room report'}
          </button>
        </div>

        <div>
          <h4 className="morning-section-label">Imported observations</h4>
          {observations.isLoading ? <p className="empty">Loading…</p> : null}
          {observations.data?.observations.map((observation) => (
            <div key={observation.id} className="morning-entry-row">
              <div>
                <strong>{observation.raw_machine_label}</strong>
                <div className="meta">{timePart(observation.start_time)}–{timePart(observation.end_time)}</div>
                <div className="meta">{observation.description}</div>
              </div>
            </div>
          ))}
          {!observations.isLoading && !observations.data?.observations.length ? (
            <p className="empty">No control-room observations imported for this date.</p>
          ) : null}
        </div>
      </div>
    </section>
  )
}
