/**
 * Global audio & TTS player supporting Play, Pause, Resume, and Stop
 * across both server-generated Sarvam audio (base64) and browser SpeechSynthesis.
 */

type Listener = () => void

class TtsPlayerManager {
  private currentAudio: HTMLAudioElement | null = null
  private currentUtterance: SpeechSynthesisUtterance | null = null
  private activeMessageId: string | null = null
  private isPausedState: boolean = false
  private isPlayingState: boolean = false
  private listeners: Set<Listener> = new Set()

  public subscribe(listener: Listener): () => void {
    this.listeners.add(listener)
    return () => {
      this.listeners.delete(listener)
    }
  }

  private notify() {
    this.listeners.forEach((fn) => fn())
  }

  public get activeId(): string | null {
    return this.activeMessageId
  }

  public get isPlaying(): boolean {
    return this.isPlayingState
  }

  public get isPaused(): boolean {
    return this.isPausedState
  }

  /**
   * Play or toggle speech for a message.
   * If already playing this message -> pause.
   * If paused for this message -> resume.
   * If playing another message -> stop other and start this one.
   */
  public toggle(messageId: string, text: string, audioBase64?: string, lang?: string) {
    if (this.activeMessageId === messageId) {
      if (this.isPlayingState) {
        this.pause()
      } else if (this.isPausedState) {
        this.resume()
      } else {
        this.start(messageId, text, audioBase64, lang)
      }
    } else {
      this.start(messageId, text, audioBase64, lang)
    }
  }

  public start(messageId: string, text: string, audioBase64?: string, lang?: string) {
    this.stop()

    this.activeMessageId = messageId
    this.isPausedState = false
    this.isPlayingState = true
    this.notify()

    // 1. If we have base64 audio from Sarvam AI, play via HTMLAudioElement
    if (audioBase64) {
      try {
        const audio = new Audio(`data:audio/wav;base64,${audioBase64}`)
        this.currentAudio = audio

        audio.onplay = () => {
          this.isPlayingState = true
          this.isPausedState = false
          this.notify()
        }

        audio.onpause = () => {
          if (!audio.ended && this.activeMessageId === messageId) {
            this.isPlayingState = false
            this.isPausedState = true
            this.notify()
          }
        }

        audio.onended = () => {
          this.stop()
        }

        audio.onerror = (e) => {
          console.warn("Audio element playback failed, falling back to speech synthesis:", e)
          this.currentAudio = null
          this.playWithSpeechSynthesis(messageId, text, lang)
        }

        audio.play().catch((err) => {
          console.warn("Audio play prevented or failed, falling back to speech synthesis:", err)
          this.currentAudio = null
          this.playWithSpeechSynthesis(messageId, text, lang)
        })
        return
      } catch (err) {
        console.warn("Could not create audio element:", err)
      }
    }

    // 2. Otherwise use browser Web Speech API
    this.playWithSpeechSynthesis(messageId, text, lang)
  }

  private playWithSpeechSynthesis(messageId: string, text: string, lang?: string) {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      this.stop()
      return
    }

    try {
      window.speechSynthesis.cancel()

      // Clean text for natural speech
      const cleanText = text
        .replace(/[*_#`~\[\]()]/g, " ")
        .replace(/https?:\/\/\S+/g, "")
        .replace(/\s+/g, " ")
        .trim()

      if (!cleanText) {
        this.stop()
        return
      }

      const utterance = new SpeechSynthesisUtterance(cleanText.slice(0, 1000))
      if (lang && (lang.includes("hi") || lang.includes("hindi"))) {
        utterance.lang = "hi-IN"
      } else {
        utterance.lang = "en-IN"
      }
      utterance.rate = 1.0

      utterance.onstart = () => {
        if (this.activeMessageId === messageId) {
          this.isPlayingState = true
          this.isPausedState = false
          this.notify()
        }
      }

      utterance.onpause = () => {
        if (this.activeMessageId === messageId) {
          this.isPlayingState = false
          this.isPausedState = true
          this.notify()
        }
      }

      utterance.onresume = () => {
        if (this.activeMessageId === messageId) {
          this.isPlayingState = true
          this.isPausedState = false
          this.notify()
        }
      }

      utterance.onend = () => {
        if (this.activeMessageId === messageId) {
          this.stop()
        }
      }

      utterance.onerror = (e) => {
        console.warn("SpeechSynthesis error:", e)
        if (this.activeMessageId === messageId) {
          this.stop()
        }
      }

      this.currentUtterance = utterance
      window.speechSynthesis.speak(utterance)
    } catch (err) {
      console.warn("SpeechSynthesis failed:", err)
      this.stop()
    }
  }

  public pause() {
    if (this.currentAudio) {
      this.currentAudio.pause()
      this.isPlayingState = false
      this.isPausedState = true
      this.notify()
    } else if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.pause()
      this.isPlayingState = false
      this.isPausedState = true
      this.notify()
    }
  }

  public resume() {
    if (this.currentAudio) {
      this.currentAudio.play().then(() => {
        this.isPlayingState = true
        this.isPausedState = false
        this.notify()
      }).catch((err) => {
        console.warn("Audio resume error:", err)
      })
    } else if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.resume()
      this.isPlayingState = true
      this.isPausedState = false
      this.notify()
    }
  }

  public stop() {
    if (this.currentAudio) {
      try {
        this.currentAudio.pause()
        this.currentAudio.currentTime = 0
      } catch {}
      this.currentAudio = null
    }

    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      try {
        window.speechSynthesis.cancel()
      } catch {}
      this.currentUtterance = null
    }

    this.activeMessageId = null
    this.isPlayingState = false
    this.isPausedState = false
    this.notify()
  }
}

export const ttsPlayer = new TtsPlayerManager()
