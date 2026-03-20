import { render, screen, fireEvent } from '@testing-library/react'
import { BulletListEditor } from '../BulletListEditor'

test('renders existing bullets as textareas', () => {
  render(<BulletListEditor value={['First bullet', 'Second bullet']} onChange={() => {}} />)
  expect(screen.getByDisplayValue('First bullet')).toBeInTheDocument()
  expect(screen.getByDisplayValue('Second bullet')).toBeInTheDocument()
})

test('calls onChange with new bullet when add is clicked', () => {
  const onChange = vi.fn()
  render(<BulletListEditor value={['Existing']} onChange={onChange} />)
  fireEvent.click(screen.getByText('+ Add bullet'))
  expect(onChange).toHaveBeenCalledWith(['Existing', ''])
})

test('calls onChange without item when remove is clicked', () => {
  const onChange = vi.fn()
  render(<BulletListEditor value={['Only bullet']} onChange={onChange} />)
  fireEvent.click(screen.getByTitle('Remove'))
  expect(onChange).toHaveBeenCalledWith([])
})

test('calls onChange with swapped items when move-up is clicked', () => {
  const onChange = vi.fn()
  render(<BulletListEditor value={['First', 'Second']} onChange={onChange} />)
  const upButtons = screen.getAllByTitle('Move up')
  fireEvent.click(upButtons[1]) // move second item up
  expect(onChange).toHaveBeenCalledWith(['Second', 'First'])
})

test('move-up disabled for first item', () => {
  render(<BulletListEditor value={['Only']} onChange={() => {}} />)
  const upButton = screen.getByTitle('Move up') as HTMLButtonElement
  expect(upButton.disabled).toBe(true)
})
