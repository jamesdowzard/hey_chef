import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { VoiceController } from './VoiceController'

describe('VoiceController', () => {
  it('renders without crashing', () => {
    render(<VoiceController />)
    // The component should render without throwing an error
    expect(document.body).toBeTruthy()
  })
  
  it('displays voice control interface', () => {
    render(<VoiceController />)
    // Look for the voice control heading
    const heading = screen.getByText('Voice Control')
    expect(heading).toBeInTheDocument()
    
    // Look for one of the buttons
    const buttons = screen.getAllByRole('button')
    expect(buttons.length).toBeGreaterThan(0)
  })
})