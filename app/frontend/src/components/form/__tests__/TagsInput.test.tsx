import { render, screen, fireEvent } from '@testing-library/react'
import { TagsInput } from '../TagsInput'

test('renders existing tags', () => {
  render(<TagsInput value={['python', 'go']} onChange={() => {}} />)
  expect(screen.getByText('python')).toBeInTheDocument()
  expect(screen.getByText('go')).toBeInTheDocument()
})

test('adds new tag on Enter', () => {
  const onChange = vi.fn()
  render(<TagsInput value={[]} onChange={onChange} />)
  const input = screen.getByPlaceholderText(/Add tag/)
  fireEvent.change(input, { target: { value: 'rust' } })
  fireEvent.keyDown(input, { key: 'Enter' })
  expect(onChange).toHaveBeenCalledWith(['rust'])
})

test('adds new tag on comma keydown', () => {
  const onChange = vi.fn()
  render(<TagsInput value={[]} onChange={onChange} />)
  const input = screen.getByPlaceholderText(/Add tag/)
  fireEvent.change(input, { target: { value: 'typescript' } })
  fireEvent.keyDown(input, { key: ',' })
  expect(onChange).toHaveBeenCalledWith(['typescript'])
})
