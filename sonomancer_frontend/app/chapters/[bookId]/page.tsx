"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import ErrorMessage from "../../components/ErrorMessage";

interface Chapter {
  index: number;
  title: string;
}

interface ChapterData {
  title: string;
  chapters: Chapter[];
}

export default function ChapterSelectionPage() {
  const params = useParams();
  const router = useRouter();
  const bookId = params.bookId as string;
  
  const [chapterData, setChapterData] = useState<ChapterData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load chapters list
  useEffect(() => {
    const fetchChapters = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/chapters/${bookId}`);
        if (!response.ok) throw new Error("Failed to fetch chapters");
        
        const data = await response.json();
        setChapterData(data);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Failed to load book chapters";
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    if (bookId) {
      fetchChapters();
    }
  }, [bookId]);

  const handleChapterSelect = (chapterIndex: number) => {
    router.push(`/reader/${bookId}?chapter=${chapterIndex}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-purple-400 mx-auto mb-4"></div>
          <p className="text-gray-300">Loading chapters...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <ErrorMessage
          message={error}
          onClose={() => router.push("/landing")}
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 p-6">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold mb-2">{chapterData?.title}</h1>
          <p className="text-gray-400">Select a chapter to begin reading with AI-generated ambience</p>
        </div>
      </header>

      {/* Chapter Grid */}
      <main className="max-w-4xl mx-auto p-6">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {chapterData?.chapters.map((chapter) => (
            <button
              key={chapter.index}
              onClick={() => handleChapterSelect(chapter.index)}
              className="bg-gray-800 hover:bg-gray-700 rounded-lg p-6 text-left transition-all duration-200 border border-gray-700 hover:border-purple-500 hover:shadow-lg hover:shadow-purple-500/20"
            >
              <div className="flex items-start justify-between mb-3">
                <span className="text-sm font-medium text-purple-400">
                  Chapter {chapter.index + 1}
                </span>
                <svg 
                  className="w-5 h-5 text-gray-400 group-hover:text-purple-400 transition-colors" 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-100 line-clamp-2">
                {chapter.title}
              </h3>
              <p className="text-sm text-gray-400 mt-2">
                Click to start reading with AI ambience
              </p>
            </button>
          ))}
        </div>

        {/* Footer Info */}
        <div className="mt-12 text-center">
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h3 className="text-lg font-semibold mb-3 text-purple-400">How It Works</h3>
            <div className="grid md:grid-cols-3 gap-4 text-sm text-gray-300">
              <div>
                <div className="font-medium mb-1">📖 Select Chapter</div>
                <div>Choose any chapter to begin</div>
              </div>
              <div>
                <div className="font-medium mb-1">🎵 AI Ambience</div>
                <div>AI analyzes the text and finds perfect ambient sounds</div>
              </div>
              <div>
                <div className="font-medium mb-1">🎧 Immersive Reading</div>
                <div>Read with contextual background audio</div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}