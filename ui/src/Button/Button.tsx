import type { ComponentPropsWithoutRef, ReactNode } from 'react'
import './Button.css'

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger'
export type ButtonSize = 'md' | 'sm'

export type ButtonProps = ComponentPropsWithoutRef<'button'> & {
  variant?: ButtonVariant
  size?: ButtonSize
  icon?: ReactNode
}

export function Button({ variant = 'secondary', size = 'md', icon, className, children, type = 'button', ...rest }: ButtonProps) {
  const classes = ['y-button', `y-button--${variant}`, size === 'sm' && 'y-button--sm', !children && 'y-button--icon-only', className]

  return (
    <button type={type} className={classes.filter(Boolean).join(' ')} {...rest}>
      {icon && (
        <span className="y-button-icon" aria-hidden="true">
          {icon}
        </span>
      )}
      {children}
    </button>
  )
}
