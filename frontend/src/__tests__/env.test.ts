import { describe, test, expect } from 'vitest'
import { API_BASE, WS_BASE } from '../lib/env'

describe('env loader', () => {
	test('exports API_BASE & WS_BASE strings', () => {
		expect(typeof API_BASE).toBe('string')
		expect(typeof WS_BASE).toBe('string')
	})
})
