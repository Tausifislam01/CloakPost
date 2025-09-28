import { describe, test, expect } from 'vitest'
import * as env from '../lib/env'

describe('env window override', () => {
	test('window.__ENV does not crash import', () => {
		// Just ensure module loads and has the expected exports
		expect(typeof env.API_BASE).toBe('string')
		expect(typeof env.WS_BASE).toBe('string')
	})
})
