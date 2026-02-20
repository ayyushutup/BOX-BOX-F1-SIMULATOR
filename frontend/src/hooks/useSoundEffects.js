/**
 * useSoundEffects — triggers audio cues for race events.
 * Uses Web Audio API for lightweight, zero-dependency sounds.
 */
import { useRef, useCallback, useEffect } from 'react'

const audioCtxRef = { current: null }
function getAudioCtx() {
    if (!audioCtxRef.current) {
        audioCtxRef.current = new (window.AudioContext || window.webkitAudioContext)()
    }
    return audioCtxRef.current
}

// Synthesize short beep/tone
function playTone(frequency, duration, type = 'sine', volume = 0.15) {
    try {
        const ctx = getAudioCtx()
        const osc = ctx.createOscillator()
        const gain = ctx.createGain()
        osc.type = type
        osc.frequency.value = frequency
        gain.gain.value = volume
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration)
        osc.connect(gain)
        gain.connect(ctx.destination)
        osc.start(ctx.currentTime)
        osc.stop(ctx.currentTime + duration)
    } catch (e) {
        // Audio not available — silent fail
    }
}

const SOUNDS = {
    overtake: () => {
        // Quick ascending two-tone
        playTone(600, 0.08, 'square', 0.1)
        setTimeout(() => playTone(900, 0.12, 'square', 0.12), 80)
    },
    pit_stop: () => {
        // Mechanical whirr then click
        playTone(200, 0.15, 'sawtooth', 0.08)
        setTimeout(() => playTone(1200, 0.05, 'square', 0.1), 150)
    },
    safety_car: () => {
        // Warning siren — two alternating tones
        playTone(800, 0.2, 'sine', 0.12)
        setTimeout(() => playTone(600, 0.2, 'sine', 0.12), 200)
        setTimeout(() => playTone(800, 0.2, 'sine', 0.1), 400)
    },
    dnf: () => {
        // Low descending tone
        playTone(400, 0.3, 'sawtooth', 0.08)
    },
    fastest_lap: () => {
        // Triple ascending bleep
        playTone(800, 0.06, 'sine', 0.1)
        setTimeout(() => playTone(1000, 0.06, 'sine', 0.1), 70)
        setTimeout(() => playTone(1300, 0.1, 'sine', 0.12), 140)
    },
}

export function useSoundEffects(enabled = true) {
    const prevEventsRef = useRef(0)

    const processEvents = useCallback((events) => {
        if (!enabled || !events?.length) return

        // Only play sounds for NEW events since last check
        const newCount = events.length
        if (newCount <= prevEventsRef.current) {
            prevEventsRef.current = newCount
            return
        }

        const newEvents = events.slice(prevEventsRef.current)
        prevEventsRef.current = newCount

        // Play sounds for new events (limit to 2 per tick to avoid cacophony)
        let played = 0
        for (const evt of newEvents) {
            if (played >= 2) break
            const type = evt.event_type?.toLowerCase()
            if (SOUNDS[type]) {
                SOUNDS[type]()
                played++
            }
        }
    }, [enabled])

    // Resume audio context on first user interaction
    useEffect(() => {
        const resume = () => {
            const ctx = audioCtxRef.current
            if (ctx?.state === 'suspended') ctx.resume()
        }
        window.addEventListener('click', resume, { once: true })
        window.addEventListener('keydown', resume, { once: true })
        return () => {
            window.removeEventListener('click', resume)
            window.removeEventListener('keydown', resume)
        }
    }, [])

    return { processEvents }
}
