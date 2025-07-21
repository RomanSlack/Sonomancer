"use client";

import { useState, useEffect } from "react";
import { XMarkIcon, MinusIcon, RectangleStackIcon, SpeakerWaveIcon, SpeakerXMarkIcon } from "@heroicons/react/24/outline";

interface AmbiencePlayerProps {
  youtubeId: string;
  mood: string;
  videoTitle: string;
  explanation: string;
}

export default function AmbiencePlayer({ youtubeId, mood, videoTitle, explanation }: AmbiencePlayerProps) {
  const [isVisible, setIsVisible] = useState(true);
  const [isMinimized, setIsMinimized] = useState(false);
  const [showExplanation, setShowExplanation] = useState(false);
  const [currentVideoId, setCurrentVideoId] = useState(youtubeId);
  const [volume, setVolume] = useState(30);
  const [isMuted, setIsMuted] = useState(false);

  // Update video ID with a small delay to prevent rapid changes
  useEffect(() => {
    const timer = setTimeout(() => {
      setCurrentVideoId(youtubeId);
    }, 100);

    return () => clearTimeout(timer);
  }, [youtubeId]);

  if (!isVisible) {
    return null;
  }

  // Simple YouTube embed URL with autoplay and volume control
  const embedUrl = `https://www.youtube.com/embed/${currentVideoId}?autoplay=1&controls=1&rel=0&showinfo=0&modestbranding=1&iv_load_policy=3&volume=${volume}&mute=${isMuted ? 1 : 0}`;

  return (
    <div className={`fixed bottom-24 right-4 bg-gray-800 rounded-lg shadow-2xl border border-gray-700 overflow-hidden z-50 transition-all duration-300 ${
      isMinimized ? 'w-64' : 'w-80'
    }`}>
      {/* Header */}
      <div className="flex items-center justify-between p-3 bg-gray-700">
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium text-purple-400 capitalize">
            {mood} Ambience
          </div>
          <div className="text-xs text-gray-400 truncate">
            {videoTitle}
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowExplanation(!showExplanation)}
            className="text-xs bg-purple-600 hover:bg-purple-700 text-white px-2 py-1 rounded transition-colors"
            title="Why this video?"
          >
            ?
          </button>
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            className="text-gray-400 hover:text-gray-300 transition-colors"
            title={isMinimized ? "Expand video" : "Minimize video"}
          >
            {isMinimized ? (
              <RectangleStackIcon className="w-4 h-4" />
            ) : (
              <MinusIcon className="w-4 h-4" />
            )}
          </button>
          <button
            onClick={() => setIsVisible(false)}
            className="text-gray-400 hover:text-gray-300 transition-colors"
          >
            <XMarkIcon className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Explanation */}
      {showExplanation && !isMinimized && (
        <div className="p-3 bg-gray-750 border-y border-gray-600">
          <p className="text-xs text-gray-300 leading-relaxed">
            {explanation}
          </p>
        </div>
      )}

      {/* Simple YouTube Embed */}
      {!isMinimized && (
        <div className="relative bg-black" style={{ aspectRatio: "16/9" }}>
          <iframe
            key={currentVideoId} // Force re-render when video changes
            src={embedUrl}
            className="w-full h-full"
            allow="autoplay; encrypted-media"
            allowFullScreen
            loading="lazy"
          />
        </div>
      )}

      {/* Volume Controls */}
      <div className="p-3 bg-gray-700 border-t border-gray-600">
        <div className="flex items-center space-x-3 mb-2">
          <button
            onClick={() => setIsMuted(!isMuted)}
            className="text-gray-400 hover:text-white transition-colors"
            title={isMuted ? "Unmute" : "Mute"}
          >
            {isMuted ? (
              <SpeakerXMarkIcon className="w-4 h-4" />
            ) : (
              <SpeakerWaveIcon className="w-4 h-4" />
            )}
          </button>
          
          <div className="flex-1">
            <input
              type="range"
              min="0"
              max="100"
              value={isMuted ? 0 : volume}
              onChange={(e) => {
                const newVolume = parseInt(e.target.value);
                setVolume(newVolume);
                if (newVolume > 0 && isMuted) {
                  setIsMuted(false);
                }
              }}
              className="w-full h-2 bg-gray-600 rounded-lg appearance-none cursor-pointer"
              disabled={isMuted}
            />
          </div>
          
          <span className="text-xs text-gray-400 w-8">
            {isMuted ? "0" : volume}%
          </span>
        </div>
        
        <div className="text-xs text-gray-500 text-center">
          {isMinimized ? "Playing in background" : "AI-selected for this chapter"}
        </div>
      </div>
    </div>
  );
}