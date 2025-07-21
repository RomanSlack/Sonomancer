"use client";

import { ChevronLeftIcon, ChevronRightIcon, SpeakerWaveIcon, SpeakerXMarkIcon } from "@heroicons/react/24/outline";

interface ReaderNavigationProps {
  currentChapter: number;
  totalChapters: number;
  chapterTitle: string;
  ambienceEnabled: boolean;
  onPreviousChapter: () => void;
  onNextChapter: () => void;
  onToggleAmbience: () => void;
}

export default function ReaderNavigation({
  currentChapter,
  totalChapters,
  chapterTitle,
  ambienceEnabled,
  onPreviousChapter,
  onNextChapter,
  onToggleAmbience,
}: ReaderNavigationProps) {
  const canGoPrevious = currentChapter > 0;
  const canGoNext = currentChapter < totalChapters - 1;

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-gray-800 border-t border-gray-700 p-4">
      <div className="max-w-4xl mx-auto flex items-center justify-between">
        {/* Previous Chapter Button */}
        <button
          onClick={onPreviousChapter}
          disabled={!canGoPrevious}
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
            canGoPrevious
              ? "bg-purple-600 hover:bg-purple-700 text-white"
              : "bg-gray-700 text-gray-400 cursor-not-allowed"
          }`}
        >
          <ChevronLeftIcon className="w-4 h-4" />
          <span className="hidden sm:inline">Previous</span>
        </button>

        {/* Chapter Info */}
        <div className="flex-1 mx-4 text-center">
          <div className="text-sm text-gray-400">
            {currentChapter + 1} / {totalChapters}
          </div>
          <div className="text-sm font-medium truncate">
            {chapterTitle}
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center space-x-2">
          {/* Ambience Toggle */}
          <button
            onClick={onToggleAmbience}
            className={`p-2 rounded-lg transition-colors ${
              ambienceEnabled
                ? "bg-purple-600 hover:bg-purple-700 text-white"
                : "bg-gray-700 hover:bg-gray-600 text-gray-300"
            }`}
            title={ambienceEnabled ? "Turn off ambience" : "Turn on ambience"}
          >
            {ambienceEnabled ? (
              <SpeakerWaveIcon className="w-5 h-5" />
            ) : (
              <SpeakerXMarkIcon className="w-5 h-5" />
            )}
          </button>

          {/* Next Chapter Button */}
          <button
            onClick={onNextChapter}
            disabled={!canGoNext}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
              canGoNext
                ? "bg-purple-600 hover:bg-purple-700 text-white"
                : "bg-gray-700 text-gray-400 cursor-not-allowed"
            }`}
          >
            <span className="hidden sm:inline">Next</span>
            <ChevronRightIcon className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}