"use client";

import { XMarkIcon } from "@heroicons/react/24/outline";

interface ErrorMessageProps {
  message: string;
  onClose: () => void;
}

export default function ErrorMessage({ message, onClose }: ErrorMessageProps) {
  return (
    <div className="fixed top-4 right-4 bg-red-600 text-white px-6 py-4 rounded-lg shadow-lg z-50 max-w-md">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium">{message}</p>
        </div>
        <button
          onClick={onClose}
          className="ml-4 text-red-200 hover:text-white transition-colors"
        >
          <XMarkIcon className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}