import { describe, test, expect } from 'vitest'
import { api } from '../lib/api'

describe('api exports', () => {
	test('has common methods', () => {
		expect(typeof api.login).toBe('function')
		expect(typeof api.register).toBe('function')
		expect(typeof api.logout).toBe('function')
		expect(typeof api.listPosts).toBe('function')
	})
})
