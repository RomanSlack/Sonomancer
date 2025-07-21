"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import FileUpload from "../components/FileUpload";
import ErrorMessage from "../components/ErrorMessage";

export default function LandingPage() {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const handleFileUpload = useCallback(async (file: File) => {
    setIsUploading(true);
    setError(null);
    
    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/upload`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Upload failed" }));
        throw new Error(errorData.detail || "Upload failed");
      }

      const result = await response.json();
      router.push(`/reader/${result.book_id}`);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Upload failed. Please try again.";
      setError(errorMessage);
    } finally {
      setIsUploading(false);
    }
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      {error && (
        <ErrorMessage
          message={error}
          onClose={() => setError(null)}
        />
      )}
      
      <div className="max-w-2xl w-full text-center">
        <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
          Sonomancer
        </h1>
        <p className="text-xl text-gray-300 mb-12">
          Transform your reading experience with AI-generated ambient soundscapes
        </p>
        
        <div className="bg-gray-800 rounded-lg p-8 shadow-2xl">
          <h2 className="text-2xl font-semibold mb-6">Upload Your Book</h2>
          <FileUpload 
            onFileSelect={handleFileUpload}
            isUploading={isUploading}
          />
          <p className="text-sm text-gray-400 mt-4">
            Supported formats: EPUB, PDF
          </p>
        </div>
      </div>
    </div>
  );
}