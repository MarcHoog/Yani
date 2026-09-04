import './Meter.css'

export type MeterProps = { value: number; max: number; warnAt?: number; label?: string }

export function Meter({ value, max, warnAt = 0.85, label }: MeterProps) {
  const ratio = max > 0 ? value / max : 0
  const width = `${Math.min(100, Math.max(0, ratio * 100))}%`

  return (
    <div className={ratio >= warnAt ? 'y-meter y-meter--warn' : 'y-meter'} role="progressbar" aria-label={label} aria-valuenow={value} aria-valuemin={0} aria-valuemax={max}>
      <span className="y-meter-fill" style={{ width }} />
    </div>
  )
}
