import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { FileTree } from '../FileTree'

const files = [
  { path: 'profile.md', name: 'profile.md', size: 123 },
  { path: 'skills.md', name: 'skills.md', size: 456 },
]

test('renders file list', () => {
  render(<FileTree files={files} selected={null} onSelect={() => {}} />)
  expect(screen.getByText('profile.md')).toBeInTheDocument()
  expect(screen.getByText('skills.md')).toBeInTheDocument()
})

test('calls onSelect with path when file is clicked', async () => {
  const onSelect = vi.fn()
  render(<FileTree files={files} selected={null} onSelect={onSelect} />)
  await userEvent.click(screen.getByText('profile.md'))
  expect(onSelect).toHaveBeenCalledWith('profile.md')
})

test('shows empty message when no files', () => {
  render(<FileTree files={[]} selected={null} onSelect={() => {}} />)
  expect(screen.getByText(/No files found/)).toBeInTheDocument()
})
