import { cn } from '@/utils/cn'

type SpinnerSize = 'sm' | 'md' | 'lg'

interface SpinnerProps {
  size?: SpinnerSize
  className?: string
}

const sizeStyles: Record<SpinnerSize, string> = {
  sm: 'h-4 w-4 border-2',
  md: 'h-8 w-8 border-2',
  lg: 'h-12 w-12 border-3',
}

export function Spinner({ size = 'md', className }: SpinnerProps) {
  return (
    <div
      className={cn(
        'animate-spin rounded-full border-gray-300 border-t-blue-600',
        sizeStyles[size],
        className
      )}
    />
  )
}

interface FullPageSpinnerProps {
  text?: string
}

export function FullPageSpinner({ text }: FullPageSpinnerProps) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-4">
      <Spinner size="lg" />
      {text && <p className="text-gray-500">{text}</p>}
    </div>
  )
}