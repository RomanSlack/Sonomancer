"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { DocumentIcon, CloudArrowUpIcon } from "@heroicons/react/24/outline";

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  isUploading: boolean;
}

export default function FileUpload({ onFileSelect, isUploading }: FileUploadProps) {
  const [isDragActive, setIsDragActive] = useState(false);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      onFileSelect(acceptedFiles[0]);
    }
  }, [onFileSelect]);

  const { getRootProps, getInputProps } = useDropzone({
    onDrop,
    accept: {
      'application/epub+zip': ['.epub'],
      'application/pdf': ['.pdf']
    },
    multiple: false,
    onDragEnter: () => setIsDragActive(true),
    onDragLeave: () => setIsDragActive(false),
  });

  if (isUploading) {
    return (
      <div className="border-2 border-dashed border-gray-600 rounded-lg p-16 text-center">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-purple-400 mx-auto mb-4"></div>
        <p className="text-lg text-gray-300">Processing your book...</p>
      </div>
    );
  }

  return (
    <div
      {...getRootProps()}
      className={`border-2 border-dashed rounded-lg p-16 text-center cursor-pointer transition-colors ${
        isDragActive 
          ? "border-purple-400 bg-purple-900/20" 
          : "border-gray-600 hover:border-gray-500"
      }`}
    >
      <input {...getInputProps()} />
      
      <div className="space-y-4">
        {isDragActive ? (
          <CloudArrowUpIcon className="w-16 h-16 text-purple-400 mx-auto" />
        ) : (
          <DocumentIcon className="w-16 h-16 text-gray-400 mx-auto" />
        )}
        
        <div>
          <p className="text-lg text-gray-300 mb-2">
            {isDragActive ? "Drop your book here" : "Drag & drop your book here"}
          </p>
          <p className="text-sm text-gray-500">
            or click to browse files
          </p>
        </div>
      </div>
    </div>
  );
}