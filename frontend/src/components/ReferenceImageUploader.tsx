'use client';

import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useThumbnailStore } from '@/stores/thumbnailStore';

export function ReferenceImageUploader() {
  const {
    referenceThumbnails,
    addReferenceThumbnail,
    removeReferenceThumbnail,
    updateReferenceThumbnailDescription,
  } = useThumbnailStore();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    acceptedFiles.forEach((file) => {
      const reader = new FileReader();
      reader.onload = () => {
        const base64 = reader.result as string;
        addReferenceThumbnail({
          data: base64,
          preview: URL.createObjectURL(file),
        });
      };
      reader.readAsDataURL(file);
    });
  }, [addReferenceThumbnail]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
      'image/webp': ['.webp'],
    },
    maxFiles: 5,
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-300">
          Reference Thumbnails
        </h3>
        <span className="text-xs text-gray-500">
          {referenceThumbnails.length}/5 uploaded
        </span>
      </div>

      <p className="text-xs text-gray-500">
        Upload example thumbnails you like. The AI will analyze their style and create similar thumbnails.
      </p>

      {/* Dropzone */}
      {referenceThumbnails.length < 5 && (
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors ${
            isDragActive
              ? 'border-purple-500 bg-purple-500/10'
              : 'border-gray-600 hover:border-gray-500'
          }`}
        >
          <input {...getInputProps()} />
          <svg
            className="mx-auto h-8 w-8 text-gray-500"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
          <p className="mt-2 text-sm text-gray-400">
            {isDragActive ? 'Drop images here...' : 'Drag & drop reference thumbnails, or click to select'}
          </p>
          <p className="mt-1 text-xs text-gray-500">
            JPG, PNG, WebP up to 10MB each
          </p>
        </div>
      )}

      {/* Uploaded Images Grid */}
      {referenceThumbnails.length > 0 && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {referenceThumbnails.map((ref, index) => (
            <div
              key={index}
              className="group relative aspect-video overflow-hidden rounded-lg bg-gray-700"
            >
              <img
                src={ref.preview || ref.data}
                alt={`Reference ${index + 1}`}
                className="h-full w-full object-cover"
              />

              {/* Remove button */}
              <button
                onClick={() => removeReferenceThumbnail(index)}
                className="absolute right-1 top-1 rounded-full bg-red-500 p-1 opacity-0 transition-opacity group-hover:opacity-100"
              >
                <svg className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>

              {/* Description overlay */}
              <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/80 to-transparent p-2 opacity-0 transition-opacity group-hover:opacity-100">
                <input
                  type="text"
                  placeholder="Add description (optional)"
                  value={ref.description || ''}
                  onChange={(e) => updateReferenceThumbnailDescription(index, e.target.value)}
                  className="w-full rounded bg-gray-800/80 px-2 py-1 text-xs text-white placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-purple-500"
                  onClick={(e) => e.stopPropagation()}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default ReferenceImageUploader;
