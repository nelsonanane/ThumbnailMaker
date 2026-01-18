'use client';

import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useThumbnailStore } from '@/stores/thumbnailStore';

export function FacePhotoUploader() {
  const {
    facePhotos,
    addFacePhoto,
    removeFacePhoto,
  } = useThumbnailStore();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    acceptedFiles.forEach((file) => {
      const reader = new FileReader();
      reader.onload = () => {
        const base64 = reader.result as string;
        addFacePhoto({
          data: base64,
          preview: URL.createObjectURL(file),
        });
      };
      reader.readAsDataURL(file);
    });
  }, [addFacePhoto]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
    },
    maxFiles: 3,
    maxSize: 5 * 1024 * 1024, // 5MB
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-300">
          Your Face Photos
        </h3>
        <span className="text-xs text-gray-500">
          {facePhotos.length}/3 uploaded
        </span>
      </div>

      <p className="text-xs text-gray-500">
        Upload face photos of people to include in your thumbnails. All faces will be used.
      </p>
      <div className="rounded-lg bg-gray-700/50 p-2 text-xs text-gray-400">
        <strong className="text-purple-400">How face photos work:</strong>
        <ul className="mt-1 ml-2 space-y-0.5">
          <li><span className="text-purple-300">First photo</span> = Primary person (main reactor/character)</li>
          <li><span className="text-gray-300">Additional photos</span> = Secondary people (replace other faces in reference)</li>
        </ul>
      </div>

      {/* Dropzone */}
      {facePhotos.length < 3 && (
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
              d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
            />
          </svg>
          <p className="mt-2 text-sm text-gray-400">
            {isDragActive ? 'Drop photos here...' : 'Drag & drop face photos, or click to select'}
          </p>
          <p className="mt-1 text-xs text-gray-500">
            JPG, PNG up to 5MB each. Clear, front-facing photos work best.
          </p>
        </div>
      )}

      {/* Uploaded Photos Grid */}
      {facePhotos.length > 0 && (
        <div className="flex flex-wrap gap-3">
          {facePhotos.map((photo, index) => (
            <div
              key={index}
              className="group relative h-20 w-20 overflow-hidden rounded-full bg-gray-700"
            >
              <img
                src={photo.preview || photo.data}
                alt={`Face ${index + 1}`}
                className="h-full w-full object-cover"
              />

              {/* Remove button */}
              <button
                onClick={() => removeFacePhoto(index)}
                className="absolute inset-0 flex items-center justify-center bg-black/50 opacity-0 transition-opacity group-hover:opacity-100"
              >
                <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>

              {/* Role badge */}
              <div className={`absolute bottom-0 left-1/2 -translate-x-1/2 transform rounded-t px-2 py-0.5 text-[10px] font-medium text-white ${
                index === 0 ? 'bg-purple-500' : 'bg-gray-600'
              }`}>
                {index === 0 ? 'Primary' : `Face ${index + 1}`}
              </div>
            </div>
          ))}
        </div>
      )}

      {facePhotos.length > 0 && (
        <p className="text-xs text-gray-500">
          {facePhotos.length === 1
            ? 'This face will be the main person in your thumbnail.'
            : `All ${facePhotos.length} faces will be used. Primary face = main character, others replace additional people in reference.`}
        </p>
      )}
    </div>
  );
}

export default FacePhotoUploader;
