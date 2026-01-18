'use client';

import { useEffect } from 'react';
import { useThumbnailStore } from '@/stores/thumbnailStore';
import { ReferenceImageUploader, FacePhotoUploader } from '@/components';

export default function Home() {
  const {
    mode,
    setMode,
    videoUrl,
    setVideoUrl,
    customPrompt,
    setCustomPrompt,
    selectedTemplate,
    setSelectedTemplate,
    addTextOverlay,
    setAddTextOverlay,
    isGenerating,
    generatedImages,
    promptUsed,
    thumbnailText,
    generationError,
    templates,
    loadTemplates,
    generateFromUrl,
    generateFromPrompt,
    clearGeneration,
    referenceThumbnails,
    facePhotos,
    clearReferenceThumbnails,
    clearFacePhotos,
  } = useThumbnailStore();

  // Load templates on mount
  useEffect(() => {
    loadTemplates();
  }, [loadTemplates]);

  const handleGenerate = () => {
    if (mode === 'url') {
      generateFromUrl();
    } else {
      generateFromPrompt();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      {/* Header */}
      <header className="border-b border-gray-700 bg-gray-900/50 backdrop-blur-sm">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-white">
              <span className="text-purple-400">AI</span> Thumbnail Generator
            </h1>
            <span className="text-sm text-gray-400">Powered by Google Imagen</span>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="grid gap-8 lg:grid-cols-2">
          {/* Left Column - Input */}
          <div className="space-y-6">
            {/* Mode Toggle */}
            <div className="flex rounded-lg bg-gray-800 p-1">
              <button
                onClick={() => setMode('url')}
                className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
                  mode === 'url'
                    ? 'bg-purple-600 text-white'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                From YouTube URL
              </button>
              <button
                onClick={() => setMode('prompt')}
                className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
                  mode === 'prompt'
                    ? 'bg-purple-600 text-white'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                From Prompt
              </button>
            </div>

            {/* Input Section */}
            <div className="rounded-xl bg-gray-800 p-6">
              {mode === 'url' ? (
                <div className="space-y-4">
                  <label className="block">
                    <span className="text-sm font-medium text-gray-300">
                      YouTube Video URL
                    </span>
                    <input
                      type="url"
                      value={videoUrl}
                      onChange={(e) => setVideoUrl(e.target.value)}
                      placeholder="https://youtube.com/watch?v=..."
                      className="mt-2 block w-full rounded-lg border border-gray-600 bg-gray-700 px-4 py-3 text-white placeholder-gray-400 focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-500/20"
                    />
                  </label>
                  <p className="text-sm text-gray-400">
                    We&apos;ll analyze the video title, description, and transcript to
                    generate the perfect thumbnail.
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  <label className="block">
                    <span className="text-sm font-medium text-gray-300">
                      Thumbnail Prompt
                    </span>
                    <textarea
                      value={customPrompt}
                      onChange={(e) => setCustomPrompt(e.target.value)}
                      placeholder="A person with shocked expression looking at a pile of money, text 'IMPOSSIBLE' in bold yellow letters..."
                      rows={4}
                      className="mt-2 block w-full rounded-lg border border-gray-600 bg-gray-700 px-4 py-3 text-white placeholder-gray-400 focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-500/20"
                    />
                  </label>
                  <p className="text-sm text-gray-400">
                    Describe your thumbnail in detail. Include expressions, text,
                    lighting, and style.
                  </p>
                </div>
              )}
            </div>

            {/* Template Selector */}
            <div className="rounded-xl bg-gray-800 p-6">
              <h3 className="mb-4 text-sm font-medium text-gray-300">
                Choose a Style
              </h3>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                {templates.map((template) => (
                  <button
                    key={template.id}
                    onClick={() =>
                      setSelectedTemplate(
                        selectedTemplate === template.id ? null : template.id
                      )
                    }
                    className={`rounded-lg border px-4 py-3 text-left text-sm transition-colors ${
                      selectedTemplate === template.id
                        ? 'border-purple-500 bg-purple-500/20 text-white'
                        : 'border-gray-600 text-gray-300 hover:border-gray-500 hover:bg-gray-700'
                    }`}
                  >
                    <span className="font-medium">{template.name}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Reference Thumbnails Uploader */}
            <div className="rounded-xl bg-gray-800 p-6">
              <ReferenceImageUploader />
              {referenceThumbnails.length > 0 && (
                <button
                  onClick={clearReferenceThumbnails}
                  className="mt-3 text-xs text-gray-400 hover:text-white"
                >
                  Clear all references
                </button>
              )}
            </div>

            {/* Face Photos Uploader */}
            <div className="rounded-xl bg-gray-800 p-6">
              <FacePhotoUploader />
              {facePhotos.length > 0 && (
                <button
                  onClick={clearFacePhotos}
                  className="mt-3 text-xs text-gray-400 hover:text-white"
                >
                  Clear all photos
                </button>
              )}
            </div>

            {/* Text Overlay Toggle */}
            {mode === 'url' && (
              <div className="rounded-xl bg-gray-800 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-medium text-gray-300">
                      Add Text Overlay
                    </h3>
                    <p className="mt-1 text-xs text-gray-500">
                      Automatically add eye-catching text based on video content
                    </p>
                  </div>
                  <button
                    onClick={() => setAddTextOverlay(!addTextOverlay)}
                    className={`relative h-6 w-11 rounded-full transition-colors ${
                      addTextOverlay ? 'bg-purple-600' : 'bg-gray-600'
                    }`}
                  >
                    <span
                      className={`absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-white transition-transform ${
                        addTextOverlay ? 'translate-x-5' : 'translate-x-0'
                      }`}
                    />
                  </button>
                </div>
              </div>
            )}

            {/* Generate Button */}
            <button
              onClick={handleGenerate}
              disabled={isGenerating || (!videoUrl && mode === 'url') || (!customPrompt && mode === 'prompt')}
              className="w-full rounded-lg bg-purple-600 px-6 py-4 text-lg font-semibold text-white transition-colors hover:bg-purple-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isGenerating ? (
                <span className="flex items-center justify-center gap-2">
                  <svg
                    className="h-5 w-5 animate-spin"
                    viewBox="0 0 24 24"
                    fill="none"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Generating...
                </span>
              ) : (
                'Generate Thumbnails'
              )}
            </button>

            {/* Error Display */}
            {generationError && (
              <div className="rounded-lg bg-red-500/20 p-4 text-red-400">
                {generationError}
              </div>
            )}
          </div>

          {/* Right Column - Results */}
          <div className="space-y-6">
            <div className="rounded-xl bg-gray-800 p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-white">
                  Generated Thumbnails
                </h3>
                {generatedImages.length > 0 && (
                  <button
                    onClick={clearGeneration}
                    className="text-sm text-gray-400 hover:text-white"
                  >
                    Clear
                  </button>
                )}
              </div>

              {generatedImages.length > 0 ? (
                <div className="space-y-6">
                  {/* Image Grid */}
                  <div className="grid grid-cols-2 gap-4">
                    {generatedImages.map((imageUrl, index) => (
                      <div
                        key={index}
                        className="group relative aspect-video overflow-hidden rounded-lg bg-gray-700"
                      >
                        <img
                          src={imageUrl}
                          alt={`Thumbnail ${index + 1}`}
                          className="h-full w-full object-cover transition-transform group-hover:scale-105"
                        />
                        <div className="absolute inset-0 flex items-center justify-center bg-black/50 opacity-0 transition-opacity group-hover:opacity-100">
                          <a
                            href={imageUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="rounded-lg bg-white px-4 py-2 text-sm font-medium text-gray-900 hover:bg-gray-100"
                          >
                            Download
                          </a>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Prompt Used */}
                  {promptUsed && (
                    <div className="space-y-2">
                      <h4 className="text-sm font-medium text-gray-400">
                        Prompt Used
                      </h4>
                      <p className="rounded-lg bg-gray-700 p-3 text-sm text-gray-300">
                        {promptUsed}
                      </p>
                    </div>
                  )}

                  {/* Suggested Text */}
                  {thumbnailText && (
                    <div className="space-y-2">
                      <h4 className="text-sm font-medium text-gray-400">
                        Suggested Text
                      </h4>
                      <p className="rounded-lg bg-purple-500/20 p-3 text-lg font-bold text-purple-300">
                        {thumbnailText}
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex aspect-video items-center justify-center rounded-lg border-2 border-dashed border-gray-600">
                  <div className="text-center">
                    <svg
                      className="mx-auto h-12 w-12 text-gray-500"
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
                      Your thumbnails will appear here
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Info Card */}
            <div className="rounded-xl bg-gray-800/50 p-6">
              <h3 className="mb-3 text-sm font-medium text-gray-300">
                How it works
              </h3>
              <ol className="space-y-2 text-sm text-gray-400">
                <li className="flex gap-2">
                  <span className="text-purple-400">1.</span>
                  Paste a YouTube URL or write a custom prompt
                </li>
                <li className="flex gap-2">
                  <span className="text-purple-400">2.</span>
                  Upload reference thumbnails to match their style
                </li>
                <li className="flex gap-2">
                  <span className="text-purple-400">3.</span>
                  Add your face photos to appear in thumbnails
                </li>
                <li className="flex gap-2">
                  <span className="text-purple-400">4.</span>
                  AI analyzes references and generates 4 variations
                </li>
                <li className="flex gap-2">
                  <span className="text-purple-400">5.</span>
                  Download your favorite thumbnail
                </li>
              </ol>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
