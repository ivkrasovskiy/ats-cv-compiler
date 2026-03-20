import { render, screen } from '@testing-library/react'
import { StatusCard } from '../StatusCard'

test('renders OK check with checkmark', () => {
  render(<StatusCard check={{ label: '✓ uv found', ok: true, raw: '✓ uv found' }} />)
  expect(screen.getByText('✓')).toBeInTheDocument()
  expect(screen.getByText('✓ uv found')).toBeInTheDocument()
})

test('renders failed check with ERROR badge', () => {
  render(<StatusCard check={{ label: '✗ data/ missing', ok: false, raw: '✗ data/ missing' }} />)
  expect(screen.getByText('ERROR')).toBeInTheDocument()
  expect(screen.getByText('✗ data/ missing')).toBeInTheDocument()
})

test('does not show ERROR badge when check passes', () => {
  render(<StatusCard check={{ label: '✓ ok', ok: true, raw: '✓ ok' }} />)
  expect(screen.queryByText('ERROR')).not.toBeInTheDocument()
})
