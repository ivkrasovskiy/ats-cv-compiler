import { render, screen } from '@testing-library/react'
import { BuildLog } from '../BuildLog'

test('shows placeholder when idle', () => {
  render(<BuildLog lines={[]} status="idle" />)
  expect(screen.getByText(/Build log will appear/)).toBeInTheDocument()
})

test('shows log lines when running', () => {
  render(<BuildLog lines={['Loading data...', 'Rendering PDF...']} status="running" />)
  expect(screen.getByText('Loading data...')).toBeInTheDocument()
  expect(screen.getByText('Rendering PDF...')).toBeInTheDocument()
})

test('shows running badge when running', () => {
  render(<BuildLog lines={[]} status="running" />)
  expect(screen.getByText('running')).toBeInTheDocument()
})

test('shows done badge when done', () => {
  render(<BuildLog lines={['Done: out/cv.pdf']} status="done" />)
  expect(screen.getByText('done')).toBeInTheDocument()
})
