import type { ComponentPropsWithoutRef, ReactNode } from 'react'
import './Field.css'

export type FieldProps = { label: string; hint?: string; error?: string; required?: boolean; children: ReactNode }

export function Field({ label, hint, error, required, children }: FieldProps) {
  return (
    <label className={error ? 'y-field y-field--error' : 'y-field'}>
      <span className="y-field-label">
        {label}
        {required && <span className="y-field-required"> *</span>}
      </span>
      {children}
      {error ? <span className="y-field-error">{error}</span> : hint && <span className="y-field-hint">{hint}</span>}
    </label>
  )
}

export function Input({ className, ...rest }: ComponentPropsWithoutRef<'input'>) {
  return <input className={className ? `y-input ${className}` : 'y-input'} {...rest} />
}

export function Textarea({ className, ...rest }: ComponentPropsWithoutRef<'textarea'>) {
  return <textarea className={className ? 'y-input y-input--area ' + className : 'y-input y-input--area'} {...rest} />
}

export function Select({ className, children, ...rest }: ComponentPropsWithoutRef<'select'>) {
  return (
    <span className="y-select">
      <select className={className ? 'y-input y-input--select ' + className : 'y-input y-input--select'} {...rest}>
        {children}
      </select>
      <svg className="y-select-chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="m6 9 6 6 6-6" />
      </svg>
    </span>
  )
}
