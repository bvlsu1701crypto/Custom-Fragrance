"use client"

import { useEffect, useRef, useState } from "react"
import { Music2, Pause, Play, Volume2, VolumeX } from "lucide-react"
import { Slider } from "@/components/ui/slider"
import { useLanguage } from "@/lib/language-context"

const BGM_STORAGE_KEY = "scentmind-bgm-settings"
const DEFAULT_VOLUME = 28

export function AmbientMusicPlayer() {
  const { language } = useLanguage()
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [volume, setVolume] = useState(DEFAULT_VOLUME)

  useEffect(() => {
    const savedSettings = window.localStorage.getItem(BGM_STORAGE_KEY)
    if (!savedSettings) {
      return
    }

    try {
      const parsed = JSON.parse(savedSettings) as { volume?: number; isMuted?: boolean }
      if (typeof parsed.volume === "number") {
        setVolume(Math.max(0, Math.min(100, parsed.volume)))
      }
      if (typeof parsed.isMuted === "boolean") {
        setIsMuted(parsed.isMuted)
      }
    } catch {
      window.localStorage.removeItem(BGM_STORAGE_KEY)
    }
  }, [])

  useEffect(() => {
    window.localStorage.setItem(BGM_STORAGE_KEY, JSON.stringify({ volume, isMuted }))
  }, [volume, isMuted])

  useEffect(() => {
    const audio = audioRef.current
    if (!audio) {
      return
    }

    audio.volume = isMuted ? 0 : volume / 100
    audio.muted = isMuted
  }, [isMuted, volume])

  useEffect(() => {
    const audio = audioRef.current
    if (!audio) {
      return
    }

    const startPlayback = async () => {
      try {
        await audio.play()
        setIsPlaying(true)
      } catch {
        setIsPlaying(false)
      }
    }

    const handleFirstInteraction = () => {
      startPlayback()
      window.removeEventListener("pointerdown", handleFirstInteraction)
      window.removeEventListener("keydown", handleFirstInteraction)
    }

    window.addEventListener("pointerdown", handleFirstInteraction, { once: true })
    window.addEventListener("keydown", handleFirstInteraction, { once: true })

    return () => {
      window.removeEventListener("pointerdown", handleFirstInteraction)
      window.removeEventListener("keydown", handleFirstInteraction)
    }
  }, [])

  const togglePlayback = async () => {
    const audio = audioRef.current
    if (!audio) {
      return
    }

    if (audio.paused) {
      try {
        await audio.play()
        setIsPlaying(true)
      } catch {
        setIsPlaying(false)
      }
      return
    }

    audio.pause()
    setIsPlaying(false)
  }

  const toggleMute = () => {
    setIsMuted((current) => !current)
  }

  const labels = language === "zh"
    ? {
        title: "入场背景音乐",
        subtitle: "柔和的环境钢琴，适合这个页面安静、感性的氛围。",
        play: "播放背景音乐",
        pause: "暂停背景音乐",
        mute: "静音背景音乐",
        unmute: "恢复背景音乐",
        volume: "背景音乐音量",
      }
    : {
        title: "Entrance BGM",
        subtitle: "Soft ambient piano selected for the page's quiet, reflective mood.",
        play: "Play background music",
        pause: "Pause background music",
        mute: "Mute background music",
        unmute: "Unmute background music",
        volume: "Background music volume",
      }

  return (
    <>
      <audio ref={audioRef} src="/audio/ambient-piano-relaxing.mp3" loop preload="auto" />
      <div className="fixed right-5 bottom-5 z-50 w-[min(320px,calc(100vw-2.5rem))] border border-border bg-background/90 p-4 shadow-[0_16px_60px_rgba(0,0,0,0.12)] backdrop-blur-md">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="flex items-center gap-2 text-[11px] uppercase tracking-[0.28em] text-muted-foreground">
              <Music2 className="h-3.5 w-3.5" />
              {labels.title}
            </p>
            <p className="mt-2 truncate font-serif text-base text-foreground">Ambient Piano Relaxing Music</p>
            <p className="mt-1 text-xs text-muted-foreground">{labels.subtitle}</p>
          </div>
          <button
            type="button"
            onClick={togglePlayback}
            className="flex h-10 w-10 shrink-0 items-center justify-center border border-foreground text-foreground transition-colors hover:bg-foreground hover:text-background"
            aria-label={isPlaying ? labels.pause : labels.play}
          >
            {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="ml-0.5 h-4 w-4" />}
          </button>
        </div>

        <div className="mt-4 flex items-center gap-3">
          <button
            type="button"
            onClick={toggleMute}
            className="flex h-9 w-9 shrink-0 items-center justify-center border border-border text-muted-foreground transition-colors hover:border-foreground hover:text-foreground"
            aria-label={isMuted ? labels.unmute : labels.mute}
          >
            {isMuted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
          </button>
          <Slider
            value={[isMuted ? 0 : volume]}
            min={0}
            max={100}
            step={1}
            onValueChange={(values) => {
              const nextVolume = values[0] ?? 0
              setVolume(nextVolume)
              setIsMuted(nextVolume === 0)
            }}
            aria-label={labels.volume}
          />
          <span className="w-10 text-right font-mono text-xs text-muted-foreground">{isMuted ? 0 : volume}%</span>
        </div>
      </div>
    </>
  )
}