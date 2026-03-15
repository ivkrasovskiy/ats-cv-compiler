import { render, screen } from '@testing-library/react'
import { PdfViewer } from '../PdfViewer'

test('shows placeholder when no filename', () => {
  render(<PdfViewer filename={null} />)
  expect(screen.getByText(/PDF preview will appear/)).toBeInTheDocument()
})

test('renders iframe with correct src when filename provided', () => {
  render(<PdfViewer filename="cv_generic.pdf" />)
  const iframe = screen.getByTitle('PDF Preview')
  expect(iframe).toHaveAttribute('src', '/api/out/cv_generic.pdf')
})

test('shows download link when filename provided', () => {
  render(<PdfViewer filename="cv_generic.pdf" />)
  const link = screen.getByRole('link', { name: 'Download' })
  expect(link).toHaveAttribute('href', '/api/out/cv_generic.pdf')
})
