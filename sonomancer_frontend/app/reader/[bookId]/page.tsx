"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import ChapterReader from "../../components/ChapterReader";
import ReaderNavigation from "../../components/ReaderNavigation";
import AmbiencePlayer from "../../components/AmbiencePlayer";
import ErrorMessage from "../../components/ErrorMessage";

interface Chapter {
  index: number;
  title: string;
}

interface ChapterContent {
  title: string;
  content: string;
  index: number;
}

interface AmbienceData {
  mood: string;
  youtube_id: string;
  video_title: string;
  explanation: string;
}

export default function ReaderPage() {
  const params = useParams();
  const bookId = params.bookId as string;
  
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [currentChapterIndex, setCurrentChapterIndex] = useState(0);
  const [chapterContent, setChapterContent] = useState<ChapterContent | null>(null);
  const [ambienceData, setAmbienceData] = useState<AmbienceData | null>(null);
  const [ambienceEnabled, setAmbienceEnabled] = useState(true);
  const [bookTitle, setBookTitle] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load chapters list
  useEffect(() => {
    const fetchChapters = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/chapters/${bookId}`);
        if (!response.ok) throw new Error("Failed to fetch chapters");
        
        const data = await response.json();
        setChapters(data.chapters);
        setBookTitle(data.title);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Failed to load book chapters";
        setError(errorMessage);
      }
    };

    if (bookId) {
      fetchChapters();
    }
  }, [bookId]);

  // Load chapter content when chapter changes
  useEffect(() => {
    const fetchChapterContent = async () => {
      setLoading(true);
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/chapter/${bookId}/${currentChapterIndex}`);
        if (!response.ok) throw new Error("Failed to fetch chapter");
        
        const data = await response.json();
        setChapterContent(data);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Failed to load chapter content";
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    if (bookId && currentChapterIndex >= 0) {
      fetchChapterContent();
    }
  }, [bookId, currentChapterIndex]);

  // Load ambience when chapter changes and ambience is enabled
  useEffect(() => {
    const fetchAmbience = async () => {
      if (!ambienceEnabled) return;
      
      try {
        // Add timestamp to force fresh analysis on each chapter change
        const timestamp = Date.now();
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/ambience/${bookId}/${currentChapterIndex}?t=${timestamp}`);
        if (!response.ok) throw new Error("Failed to fetch ambience");
        
        const data = await response.json();
        setAmbienceData(data);
        console.log(`🎵 New ambience loaded for chapter ${currentChapterIndex}:`, data);
      } catch (err) {
        console.error('Ambience fetch error:', err);
        // Don't show error for ambience failures, just continue without it
        setAmbienceData(null);
      }
    };

    if (bookId && currentChapterIndex >= 0 && ambienceEnabled) {
      // Clear previous ambience data immediately when switching chapters
      setAmbienceData(null);
      fetchAmbience();
    } else {
      setAmbienceData(null);
    }
  }, [bookId, currentChapterIndex, ambienceEnabled]);

  const handleChapterChange = (newIndex: number) => {
    if (newIndex >= 0 && newIndex < chapters.length) {
      setCurrentChapterIndex(newIndex);
    }
  };

  const handlePreviousChapter = () => {
    handleChapterChange(currentChapterIndex - 1);
  };

  const handleNextChapter = () => {
    handleChapterChange(currentChapterIndex + 1);
  };

  if (chapters.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-purple-400"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      {error && (
        <ErrorMessage
          message={error}
          onClose={() => setError(null)}
        />
      )}
      
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 p-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <h1 className="text-xl font-semibold truncate">{bookTitle}</h1>
          <div className="text-sm text-gray-400">
            Chapter {currentChapterIndex + 1} of {chapters.length}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="pb-24">
        <ChapterReader 
          content={chapterContent}
          loading={loading}
        />
      </main>

      {/* Ambience Player */}
      {ambienceEnabled && ambienceData && (
        <AmbiencePlayer 
          youtubeId={ambienceData.youtube_id}
          mood={ambienceData.mood}
          videoTitle={ambienceData.video_title}
          explanation={ambienceData.explanation}
        />
      )}

      {/* Navigation Footer */}
      <ReaderNavigation
        currentChapter={currentChapterIndex}
        totalChapters={chapters.length}
        chapterTitle={chapters[currentChapterIndex]?.title || ""}
        ambienceEnabled={ambienceEnabled}
        onPreviousChapter={handlePreviousChapter}
        onNextChapter={handleNextChapter}
        onToggleAmbience={() => setAmbienceEnabled(!ambienceEnabled)}
      />
    </div>
  );
}