"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { XMarkIcon, SpeakerWaveIcon, SpeakerXMarkIcon, MinusIcon, RectangleStackIcon } from "@heroicons/react/24/outline";
import { loadYouTubeAPI, isYouTubeAPIReady } from "../lib/youtube-api";

interface AmbiencePlayerProps {
  youtubeId: string;
  mood: string;
  videoTitle: string;
  explanation: string;
}

export default function AmbiencePlayer({ youtubeId, mood, videoTitle, explanation }: AmbiencePlayerProps) {
  const [isVisible, setIsVisible] = useState(true);
  const [isMinimized, setIsMinimized] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [volume, setVolume] = useState(15);
  const [isMuted, setIsMuted] = useState(false);
  const [showExplanation, setShowExplanation] = useState(false);
  const [player, setPlayer] = useState<any>(null);
  const playerRef = useRef<HTMLDivElement>(null);
  const previousVideoId = useRef<string>("");

  // Initialize player function
  const initializePlayer = useCallback(() => {
    if (!playerRef.current || !isYouTubeAPIReady()) {
      return;
    }

    // Clear any existing player
    if (player) {
      try {
        player.destroy();
      } catch (e) {
        console.warn('Error destroying existing player:', e);
      }
      setPlayer(null);
    }

    // Clear container
    playerRef.current.innerHTML = '';

    try {
      const newPlayer = new window.YT.Player(playerRef.current, {
        height: '180',
        width: '320',
        videoId: youtubeId,
        playerVars: {
          autoplay: 1,
          controls: 1,
          rel: 0,
          showinfo: 0,
          iv_load_policy: 3,
          modestbranding: 1,
        },
        events: {
          onReady: (event: any) => {
            try {
              event.target.setVolume(volume);
              if (isMuted) {
                event.target.mute();
              }
              setIsLoading(false);
              setPlayer(event.target);
            } catch (e) {
              console.warn('Error setting up player:', e);
              setIsLoading(false);
            }
          },
          onStateChange: (event: any) => {
            if (event.data === window.YT.PlayerState.PLAYING) {
              setIsLoading(false);
            }
          },
          onError: (event: any) => {
            console.warn('YouTube player error:', event);
            setIsLoading(false);
          },
        },
      });
      previousVideoId.current = youtubeId;
    } catch (error) {
      console.error('Error creating player:', error);
      setIsLoading(false);
    }
  }, [youtubeId, volume, isMuted, player]);

  // Load YouTube API
  useEffect(() => {
    let mounted = true;

    const setupPlayer = async () => {
      try {
        await loadYouTubeAPI();
        if (mounted) {
          initializePlayer();
        }
      } catch (error) {
        console.error('Failed to load YouTube API:', error);
        if (mounted) {
          setIsLoading(false);
        }
      }
    };

    setupPlayer();

    return () => {
      mounted = false;
      if (player) {
        try {
          player.destroy();
        } catch (e) {
          console.warn('Error destroying player on unmount:', e);
        }
      }
    };
  }, [initializePlayer]);

  // Handle video changes
  useEffect(() => {
    if (player && previousVideoId.current !== youtubeId) {
      setIsLoading(true);
      try {
        player.loadVideoById(youtubeId);
        previousVideoId.current = youtubeId;
      } catch (error) {
        console.warn('Error loading new video:', error);
        setIsLoading(false);
      }
    }
  }, [youtubeId, player]);

  const handleVolumeChange = (newVolume: number) => {
    setVolume(newVolume);
    if (player && typeof player.setVolume === 'function') {
      try {
        player.setVolume(newVolume);
        if (newVolume > 0 && isMuted) {
          setIsMuted(false);
          player.unMute();
        }
      } catch (e) {
        console.warn('Error setting volume:', e);
      }
    }
  };

  const toggleMute = () => {
    const newMuted = !isMuted;
    setIsMuted(newMuted);
    if (player) {
      try {
        if (newMuted && typeof player.mute === 'function') {
          player.mute();
        } else if (!newMuted && typeof player.unMute === 'function') {
          player.unMute();
        }
      } catch (e) {
        console.warn('Error toggling mute:', e);
      }
    }
  };

  if (!isVisible) {
    return null;
  }

  return (
    <div className={`fixed bottom-24 right-4 bg-gray-800 rounded-lg shadow-2xl border border-gray-700 overflow-hidden z-50 transition-all duration-300 ${
      isMinimized ? 'w-72' : 'w-80'
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

      {/* Video Player - Hide visually when minimized but keep DOM element */}
      <div 
        className={`relative bg-black transition-all duration-300 ${
          isMinimized ? 'h-0 overflow-hidden' : 'block'
        }`} 
        style={!isMinimized ? { aspectRatio: "16/9" } : { height: 0 }}
      >
        {isLoading && !isMinimized && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-400"></div>
          </div>
        )}
        
        <div 
          ref={playerRef} 
          className="w-full h-full"
          style={{ height: isMinimized ? '180px' : '100%', opacity: isMinimized ? 0 : 1 }}
        />
      </div>

      {/* Volume Controls */}
      <div className="p-3 bg-gray-700 border-t border-gray-600">
        <div className="flex items-center space-x-3">
          <button
            onClick={toggleMute}
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
              onChange={(e) => handleVolumeChange(parseInt(e.target.value))}
              className="w-full h-2 bg-gray-600 rounded-lg appearance-none cursor-pointer slider"
              disabled={isMuted}
            />
          </div>
          
          <span className="text-xs text-gray-400 w-8">
            {isMuted ? "0" : volume}%
          </span>
        </div>
        
        <div className="text-xs text-gray-500 text-center mt-2">
          {isMinimized ? "Playing in background" : "AI-selected for this chapter"}
        </div>
      </div>
    </div>
  );
}