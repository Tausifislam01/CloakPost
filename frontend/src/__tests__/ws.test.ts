import { describe, test, expect } from 'vitest'
import { chatSocketByPeerId } from '../lib/ws'

describe('ws helper', () => {
	test('chatSocketByPeerId returns a WebSocket-like object when given id or string', () => {
		// We cannot open real sockets in tests, but the constructor should run.
		// Create with a dummy id and ensure it constructs a WebSocket instance.
		const ws1 = chatSocketByPeerId('alice')
		const ws2 = chatSocketByPeerId(123)
		expect(ws1).toBeDefined()
		expect(ws2).toBeDefined()
		// Close if possible
		try { ws1.close(); ws2.close() } catch {}
	})
})
