import { useEffect, useState, useCallback } from "react";
import { useParams } from "react-router-dom";
import { Volume2, Play, Video, X, Film, Download, SkipForward, AlertCircle, CheckCircle, Clock, Wand2, Sparkles, Zap } from "lucide-react";

type Block = {
  id: string;
  text: string;
  target_sec: number;
  voice_id?: string;
  audio_url?: string;
  video_url?: string;
  user_prompt?: string;
};

type Voice = {
  voice_id: string;
  name: string;
  preview_url?: string;
};

export default function ProjectCanvasPage() {
  const { name } = useParams<{ name: string }>();
  const [blocks, setBlocks] = useState<Block[]>([]);
  const [voices, setVoices] = useState<Voice[]>([]);
  const [loading, setLoading] = useState(true);
  const [fullAudioUrl, setFullAudioUrl] = useState<string | null>(null);
  const [fullVideoUrl, setFullVideoUrl] = useState<string | null>(null);
  const [muxedVideoUrl, setMuxedVideoUrl] = useState<string | null>(null);
  const [isGeneratingAllVideos, setIsGeneratingAllVideos] = useState(false);
  const [isStitchingVideo, setIsStitchingVideo] = useState(false);
  const [isMuxingAudio, setIsMuxingAudio] = useState(false);
  const [selectedVideo, setSelectedVideo] = useState<string | null>(null);
  const [isPhoneVisible, setIsPhoneVisible] = useState(false);
  const [phonePosition, setPhonePosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [generatingBlocks, setGeneratingBlocks] = useState<Set<number>>(new Set());
  const [generatingAudio, setGeneratingAudio] = useState<Set<number>>(new Set());
  const [activeStep, setActiveStep] = useState<'videos' | 'stitch' | 'mux' | 'complete' | null>(null);

  const loadProject = useCallback(async () => {
    if (!name) return;
    setLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/projects/${encodeURIComponent(name)}`);
      const data = await res.json();
      const initialBlocks = data.blocks.map((b: any, i: number) => ({
        ...b,
        id: b.id ?? `block_${i}`,
        voice_id: '',
        audio_url: '',
        video_url: '',
        user_prompt: '',
      }));
      setBlocks(initialBlocks);
    } catch (err) {
      console.error("Failed to load project", err);
    } finally {
      setLoading(false);
    }
  }, [name]);

  const loadVoices = useCallback(async () => {
    try {
      const res = await fetch("http://localhost:8000/elevenlabs/voices");
      const data = await res.json();
      setVoices(data.voices || []);
    } catch (err) {
      console.error("Failed to load voices", err);
    }
  }, []);

  const loadAudioMeta = useCallback(async () => {
    if (!name) return;
    try {
      const res = await fetch(`http://localhost:8000/static/${name}/media/audio/audio.json?${Date.now()}`);
      if (!res.ok) return;
      const meta = await res.json();

      const voiceCounts: Record<string, number> = {};
      Object.values(meta).forEach((entry: any) => {
        if (entry.voice_id) {
          voiceCounts[entry.voice_id] = (voiceCounts[entry.voice_id] || 0) + 1;
        }
      });
      const dominantVoice = Object.entries(voiceCounts).sort((a, b) => b[1] - a[1])[0]?.[0];

      setBlocks(prev =>
        prev.map(block => {
          const metaEntry = meta[block.id] || {};
          return {
            ...block,
            audio_url: metaEntry.url || '',
            voice_id: metaEntry.voice_id || block.voice_id || dominantVoice || '',
          };
        })
      );
    } catch (err) {
      console.error("Failed to load audio metadata", err);
    }
  }, [name]);

  const loadVideoMeta = useCallback(async () => {
    if (!name) return;
    try {
      const res = await fetch(`http://localhost:8000/static/${name}/media/video/video.json?${Date.now()}`);
      if (!res.ok) return;
      const meta = await res.json();

      setBlocks(prev =>
        prev.map(block => {
          const metaEntry = meta[block.id] || {};
          return {
            ...block,
            video_url: metaEntry.url || block.video_url || '',
          };
        })
      );
    } catch (err) {
      console.error("Failed to load video metadata", err);
    }
  }, [name]);

  const checkFullAudioExists = useCallback(async () => {
    if (!name) return;
    const url = `http://localhost:8000/static/${name}/media/audio/full_audio.mp3`;
    try {
      const res = await fetch(url, { method: 'HEAD' });
      if (res.ok) {
        setFullAudioUrl(`${url}?t=${Date.now()}`);
      } else {
        setFullAudioUrl(null);
      }
    } catch (err) {
      setFullAudioUrl(null);
    }
  }, [name]);

  const checkFullVideoExists = useCallback(async () => {
    if (!name) return;
    const url = `http://localhost:8000/static/${name}/media/video/final_video.mp4`;
    try {
      const res = await fetch(url, { method: 'HEAD' });
      if (res.ok) {
        setFullVideoUrl(`${url}?t=${Date.now()}`);
      } else {
        setFullVideoUrl(null);
      }
    } catch (err) {
      setFullVideoUrl(null);
    }
  }, [name]);

  const checkMuxedVideoExists = useCallback(async () => {
    if (!name) return;
    const url = `http://localhost:8000/static/${name}/media/mux/full_video.mp4`;
    try {
      const res = await fetch(url, { method: 'HEAD' });
      if (res.ok) {
        setMuxedVideoUrl(`${url}?t=${Date.now()}`);
      } else {
        setMuxedVideoUrl(null);
      }
    } catch (err) {
      setMuxedVideoUrl(null);
    }
  }, [name]);

  const checkVideoExists = useCallback(async (blockId: string): Promise<string | null> => {
    if (!name) return null;
    const url = `http://localhost:8000/static/${name}/media/video/${blockId}.mp4`;
    try {
      const res = await fetch(url, { method: 'HEAD' });
      if (res.ok) return `${url}?t=${Date.now()}`;
    } catch (_) {}
    return null;
  }, [name]);

  const handleGenerateVideo = async (index: number) => {
    const block = blocks[index];
    if (!name || !block.text) return;

    setGeneratingBlocks(prev => new Set(prev).add(index));

    const payload = {
      project_name: name,
      block_id: block.id,
      block_text: block.text,
      user_prompt: block.user_prompt || "",
    };

    try {
      const res = await fetch("http://localhost:8000/generate_block_video", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (data.success) {
        const videoUrl = await checkVideoExists(block.id);
        const updated = [...blocks];
        updated[index].video_url = videoUrl || '';
        setBlocks(updated);
      } else {
        console.error("Video generation failed:", data);
      }
    } catch (err) {
      console.error("Failed to generate video", err);
    } finally {
      setGeneratingBlocks(prev => {
        const newSet = new Set(prev);
        newSet.delete(index);
        return newSet;
      });
    }
  };

  const handlePlayVideo = (videoUrl: string) => {
    setSelectedVideo(videoUrl);
    setIsPhoneVisible(true);
    setPhonePosition({ x: window.innerWidth - 280, y: window.innerHeight - 580 });
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragOffset({
      x: e.clientX - phonePosition.x,
      y: e.clientY - phonePosition.y
    });
  };

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (isDragging) {
      const newX = e.clientX - dragOffset.x;
      const newY = e.clientY - dragOffset.y;
      
      const maxX = window.innerWidth - 280;
      const maxY = window.innerHeight - 580;
      
      setPhonePosition({
        x: Math.max(0, Math.min(newX, maxX)),
        y: Math.max(0, Math.min(newY, maxY))
      });
    }
  }, [isDragging, dragOffset]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, dragOffset]);

  useEffect(() => {
    loadProject();
    loadVoices();
  }, [loadProject, loadVoices]);

  useEffect(() => {
    if (blocks.length > 0) {
      loadAudioMeta();
      loadVideoMeta();
    }
  }, [blocks.length, loadAudioMeta, loadVideoMeta]);

  useEffect(() => {
    checkFullAudioExists();
    checkFullVideoExists();
    checkMuxedVideoExists();
  }, [checkFullAudioExists, checkFullVideoExists, checkMuxedVideoExists]);

  const handleTextChange = (index: number, newText: string) => {
    const updated = [...blocks];
    updated[index].text = newText;
    setBlocks(updated);
  };

  const handlePromptChange = (index: number, prompt: string) => {
    const updated = [...blocks];
    updated[index].user_prompt = prompt;
    setBlocks(updated);
  };

  const handleVoiceChange = (index: number, voiceId: string) => {
    const updated = [...blocks];
    updated[index].voice_id = voiceId;
    setBlocks(updated);
  };

  const handleGenerateAudio = async (index: number) => {
    const block = blocks[index];
    if (!block.voice_id) {
      alert("Please select a voice before generating audio.");
      return;
    }
    if (!name || !block.text) return;

    setGeneratingAudio(prev => new Set(prev).add(index));

    const payload = {
      project_name: name,
      block_id: block.id,
      text: block.text,
      voice_id: block.voice_id,
    };

    try {
      const res = await fetch("http://localhost:8000/elevenlabs/generate_audio", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (data.success) {
        const updated = [...blocks];
        const metaRes = await fetch(`http://localhost:8000/static/${name}/media/audio/audio.json?${Date.now()}`);
        const meta = await metaRes.json();
        updated[index].audio_url = meta[block.id]?.url || '';
        updated[index].voice_id = meta[block.id]?.voice_id || block.voice_id || '';
        setBlocks(updated);
      } else {
        console.error("Audio generation failed:", data);
      }
    } catch (err) {
      console.error("Failed to generate audio", err);
    } finally {
      setGeneratingAudio(prev => {
        const newSet = new Set(prev);
        newSet.delete(index);
        return newSet;
      });
    }
  };

  const handleGenerateFullAudio = async () => {
    if (!name) return;
    try {
      const res = await fetch("http://localhost:8000/elevenlabs/generate_full_audio", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ project_name: name }),
      });

      const data = await res.json();
      if (data.success) {
        checkFullAudioExists();
      } else {
        console.error("Full audio generation failed:", data);
      }
    } catch (err) {
      console.error("Failed to generate full audio", err);
    }
  };

  const handleGenerateAllVideos = async () => {
    setIsGeneratingAllVideos(true);
    setActiveStep('videos');
    try {
      const promises = blocks.map(async (block, index) => {
        const payload = {
          project_name: name,
          block_id: block.id,
          block_text: block.text,
          user_prompt: block.user_prompt || "",
        };

        const res = await fetch("http://localhost:8000/generate_block_video", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        if (res.ok) {
          const videoUrl = await checkVideoExists(block.id);
          const updated = [...blocks];
          updated[index].video_url = videoUrl || '';
          setBlocks(updated);
        }
      });

      await Promise.all(promises);
      loadVideoMeta();
    } catch (err) {
      console.error("Failed to generate all videos", err);
    } finally {
      setIsGeneratingAllVideos(false);
      setActiveStep(null);
    }
  };

  const handleStitchVideo = async () => {
    if (!name) return;
    setIsStitchingVideo(true);
    setActiveStep('stitch');
    try {
      const res = await fetch("http://localhost:8000/generate_full_video", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ project_name: name }),
      });

      const data = await res.json();
      if (data.success) {
        setTimeout(() => {
          checkFullVideoExists();
        }, 2000);
      } else {
        console.error("Video stitching failed:", data);
      }
    } catch (err) {
      console.error("Failed to stitch videos", err);
    } finally {
      setIsStitchingVideo(false);
      setActiveStep(null);
    }
  };

  const handleMuxAudioVideo = async () => {
    if (!name) return;
    setIsMuxingAudio(true);
    setActiveStep('mux');
    try {
      const res = await fetch("http://localhost:8000/mux_audio_video", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ project_name: name }),
      });

      const data = await res.json();
      if (data.success) {
        setTimeout(() => {
          checkMuxedVideoExists();
          setActiveStep('complete');
        }, 2000);
      } else {
        console.error("Audio/video muxing failed:", data);
      }
    } catch (err) {
      console.error("Failed to mux audio and video", err);
    } finally {
      setIsMuxingAudio(false);
    }
  };

  const playPreview = (voiceId: string) => {
    const voice = voices.find(v => v.voice_id === voiceId);
    if (voice?.preview_url) {
      const audio = new Audio(voice.preview_url);
      audio.play();
    }
  };

  // Calculate progress
  const videosGenerated = blocks.filter(b => b.video_url).length;
  const audiosGenerated = blocks.filter(b => b.audio_url).length;
  const videoProgress = (videosGenerated / blocks.length) * 100;
  const audioProgress = (audiosGenerated / blocks.length) * 100;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Enhanced Header */}
      <header className="sticky top-0 z-20 bg-white/90 backdrop-blur-xl border-b border-gray-200/50 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              <div className="relative">
                <div className="w-12 h-12 bg-gradient-to-r from-purple-600 via-pink-600 to-blue-600 rounded-2xl flex items-center justify-center shadow-lg">
                  <Film className="w-6 h-6 text-white" />
                </div>
                <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-white animate-pulse"></div>
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent">{name}</h1>
                <p className="text-sm text-gray-500 flex items-center gap-2">
                  <Sparkles className="w-4 h-4" />
                  AI Video Production Studio
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              {/* Progress Indicators */}
              <div className="hidden md:flex items-center gap-4 mr-4">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-blue-500 to-blue-600 transition-all duration-300"
                      style={{ width: `${audioProgress}%` }}
                    ></div>
                  </div>
                  <span className="text-xs text-gray-600">{audiosGenerated}/{blocks.length} Audio</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-8 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-green-500 to-green-600 transition-all duration-300"
                      style={{ width: `${videoProgress}%` }}
                    ></div>
                  </div>
                  <span className="text-xs text-gray-600">{videosGenerated}/{blocks.length} Video</span>
                </div>
              </div>

              <button
                onClick={handleGenerateFullAudio}
                className="bg-gradient-to-r from-blue-500 to-blue-600 text-white px-4 py-2.5 rounded-xl hover:from-blue-600 hover:to-blue-700 transition-all duration-200 shadow-lg hover:shadow-xl font-medium flex items-center gap-2 hover:scale-105"
              >
                <Volume2 size={16} />
                <span className="hidden sm:inline">Full Audio</span>
              </button>

              <button
                onClick={handleGenerateAllVideos}
                disabled={isGeneratingAllVideos}
                className="bg-gradient-to-r from-green-500 to-green-600 text-white px-4 py-2.5 rounded-xl hover:from-green-600 hover:to-green-700 transition-all duration-200 shadow-lg hover:shadow-xl font-medium flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105"
              >
                <Video size={16} />
                <span className="hidden sm:inline">{isGeneratingAllVideos ? 'Generating...' : 'All Videos'}</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Enhanced Production Pipeline */}
        <div className="mb-8 bg-white/70 backdrop-blur-sm rounded-3xl shadow-xl border border-white/50 p-8 hover:shadow-2xl transition-all duration-300">
          <div className="text-center mb-8">
            <div className="inline-flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-2xl flex items-center justify-center">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <h2 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                Production Pipeline
              </h2>
            </div>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Transform your script into a complete video with our AI-powered workflow
            </p>
          </div>

          {/* Pipeline Steps */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            {/* Step 1 */}
            <div className={`relative p-6 rounded-2xl border-2 transition-all duration-300 ${
              activeStep === 'videos' 
                ? 'border-orange-300 bg-orange-50 shadow-lg scale-105' 
                : 'border-gray-200 bg-white hover:border-orange-200 hover:shadow-md'
            }`}>
              <div className="flex items-center gap-3 mb-4">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-300 ${
                  videosGenerated === blocks.length
                    ? 'bg-green-100 text-green-600'
                    : activeStep === 'videos'
                    ? 'bg-orange-100 text-orange-600'
                    : 'bg-gray-100 text-gray-600'
                }`}>
                  {videosGenerated === blocks.length ? <CheckCircle size={20} /> : <Video size={20} />}
                </div>
                <h3 className="font-bold text-lg">Generate Videos</h3>
              </div>
              <p className="text-gray-600 mb-4">Create AI videos from all text blocks</p>
              <button
                onClick={handleGenerateAllVideos}
                disabled={isGeneratingAllVideos}
                className="w-full bg-gradient-to-r from-orange-500 to-orange-600 text-white py-3 rounded-xl hover:from-orange-600 hover:to-orange-700 transition-all duration-200 font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isGeneratingAllVideos ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    Generating...
                  </>
                ) : (
                  <>
                    <Wand2 size={18} />
                    Generate All ({videosGenerated}/{blocks.length})
                  </>
                )}
              </button>
              {activeStep === 'videos' && (
                <div className="absolute -top-2 -right-2 w-6 h-6 bg-orange-500 rounded-full animate-pulse"></div>
              )}
            </div>

            {/* Step 2 */}
            <div className={`relative p-6 rounded-2xl border-2 transition-all duration-300 ${
              activeStep === 'stitch' 
                ? 'border-purple-300 bg-purple-50 shadow-lg scale-105' 
                : 'border-gray-200 bg-white hover:border-purple-200 hover:shadow-md'
            }`}>
              <div className="flex items-center gap-3 mb-4">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-300 ${
                  fullVideoUrl
                    ? 'bg-green-100 text-green-600'
                    : activeStep === 'stitch'
                    ? 'bg-purple-100 text-purple-600'
                    : 'bg-gray-100 text-gray-600'
                }`}>
                  {fullVideoUrl ? <CheckCircle size={20} /> : <Film size={20} />}
                </div>
                <h3 className="font-bold text-lg">Stitch Videos</h3>
              </div>
              <p className="text-gray-600 mb-4">Combine all video blocks into one</p>
              <button
                onClick={handleStitchVideo}
                disabled={isStitchingVideo || !blocks.some(b => b.video_url)}
                className="w-full bg-gradient-to-r from-purple-500 to-purple-600 text-white py-3 rounded-xl hover:from-purple-600 hover:to-purple-700 transition-all duration-200 font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isStitchingVideo ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    Stitching...
                  </>
                ) : (
                  <>
                    <SkipForward size={18} />
                    Stitch Together
                  </>
                )}
              </button>
              {activeStep === 'stitch' && (
                <div className="absolute -top-2 -right-2 w-6 h-6 bg-purple-500 rounded-full animate-pulse"></div>
              )}
            </div>

            {/* Step 3 */}
            <div className={`relative p-6 rounded-2xl border-2 transition-all duration-300 ${
              activeStep === 'mux' || activeStep === 'complete'
                ? 'border-pink-300 bg-pink-50 shadow-lg scale-105' 
                : 'border-gray-200 bg-white hover:border-pink-200 hover:shadow-md'
            }`}>
              <div className="flex items-center gap-3 mb-4">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-300 ${
                  muxedVideoUrl
                    ? 'bg-green-100 text-green-600'
                    : activeStep === 'mux' || activeStep === 'complete'
                    ? 'bg-pink-100 text-pink-600'
                    : 'bg-gray-100 text-gray-600'
                }`}>
                  {muxedVideoUrl ? <CheckCircle size={20} /> : <Volume2 size={20} />}
                </div>
                <h3 className="font-bold text-lg">Add Audio</h3>
              </div>
              <p className="text-gray-600 mb-4">Combine video with audio track</p>
              <button
                onClick={handleMuxAudioVideo}
                disabled={isMuxingAudio || !fullVideoUrl || !fullAudioUrl}
                className="w-full bg-gradient-to-r from-pink-500 to-pink-600 text-white py-3 rounded-xl hover:from-pink-600 hover:to-pink-700 transition-all duration-200 font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isMuxingAudio ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    Muxing...
                  </>
                ) : (
                  <>
                    <Sparkles size={18} />
                    Mux Audio
                  </>
                )}
              </button>
              {(activeStep === 'mux' || activeStep === 'complete') && (
                <div className="absolute -top-2 -right-2 w-6 h-6 bg-pink-500 rounded-full animate-pulse"></div>
              )}
            </div>
          </div>

          {/* Progress Status */}
          {(isGeneratingAllVideos || isStitchingVideo || isMuxingAudio) && (
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl p-6 text-center border border-blue-200">
              <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <h3 className="text-xl font-bold text-blue-900 mb-2">
                {isGeneratingAllVideos && "🎬 Generating Videos"}
                {isStitchingVideo && "🎞️ Stitching Videos"}
                {isMuxingAudio && "🎧 Adding Audio"}
              </h3>
              <p className="text-blue-700">
                {isGeneratingAllVideos && "Creating AI videos from your script blocks..."}
                {isStitchingVideo && "Combining all video blocks into one seamless video..."}
                {isMuxingAudio && "Synchronizing audio track with video content..."}
              </p>
              <div className="mt-4 flex items-center justify-center gap-2 text-sm text-blue-600">
                <Clock size={16} />
                This may take a few minutes
              </div>
            </div>
          )}
        </div>

        {/* Final Video Showcase */}
        {muxedVideoUrl && (
          <div className="mb-8 bg-gradient-to-r from-emerald-50 via-teal-50 to-cyan-50 rounded-3xl shadow-xl border border-emerald-200 p-8 hover:shadow-2xl transition-all duration-300">
            <div className="text-center mb-6">
              <div className="inline-flex items-center gap-3 mb-4">
                <div className="w-12 h-12 bg-gradient-to-r from-emerald-500 to-teal-500 rounded-2xl flex items-center justify-center animate-pulse">
                  <CheckCircle className="w-6 h-6 text-white" />
                </div>
                <h2 className="text-3xl font-bold bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent">
                  🎉 Your Video is Ready!
                </h2>
              </div>
              <p className="text-gray-600 text-lg">Complete with audio and visual effects</p>
            </div>
            
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <button
                onClick={() => handlePlayVideo(muxedVideoUrl)}
                className="group flex items-center gap-3 bg-gradient-to-r from-emerald-500 to-teal-500 text-white px-8 py-4 rounded-2xl hover:from-emerald-600 hover:to-teal-600 transition-all duration-200 font-bold shadow-lg hover:shadow-xl transform hover:scale-105"
              >
                <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center group-hover:rotate-12 transition-transform duration-200">
                  <Play size={20} />
                </div>
                Watch Final Video
              </button>
              <a
                href={muxedVideoUrl}
                download="final_video.mp4"
                className="group flex items-center gap-3 bg-white text-emerald-600 px-8 py-4 rounded-2xl hover:bg-emerald-50 transition-all duration-200 font-bold shadow-lg hover:shadow-xl border border-emerald-200 transform hover:scale-105"
              >
                <Download size={20} className="group-hover:animate-bounce" />
                Download Video
              </a>
            </div>
          </div>
        )}

        {/* Media Previews */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Full Audio Preview */}
          {fullAudioUrl && (
            <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-lg border border-white/50 p-6 hover:shadow-xl transition-all duration-300">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-xl flex items-center justify-center">
                  <Volume2 size={20} className="text-white" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-gray-900">Complete Audio Track</h3>
                  <p className="text-sm text-gray-500">Full narration ready for video</p>
                </div>
              </div>
              <audio 
                controls 
                src={fullAudioUrl} 
                className="w-full h-12 rounded-xl shadow-sm bg-gradient-to-r from-blue-50 to-indigo-50"
              />
            </div>
          )}

          {/* Raw Video Preview */}
          {fullVideoUrl && !muxedVideoUrl && (
            <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-lg border border-white/50 p-6 hover:shadow-xl transition-all duration-300">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl flex items-center justify-center">
                    <Video size={20} className="text-white" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-gray-900">Stitched Video</h3>
                    <p className="text-sm text-gray-500">Silent video ready for audio</p>
                  </div>
                </div>
                <button
                  onClick={() => handlePlayVideo(fullVideoUrl)}
                  className="flex items-center gap-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white px-4 py-2 rounded-xl hover:from-purple-600 hover:to-pink-600 transition-all duration-200 font-medium shadow-lg transform hover:scale-105"
                >
                  <Play size={16} />
                  Preview
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Script Blocks */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-6"></div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Loading Your Project</h3>
              <p className="text-gray-600">Fetching script blocks and media...</p>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">📝 Script Blocks</h2>
              <p className="text-gray-600">Edit content and generate individual audio/video</p>
            </div>

            {blocks.map((block, i) => (
              <div key={block.id} className="group bg-white/70 backdrop-blur-sm rounded-2xl shadow-lg border border-white/50 overflow-hidden hover:shadow-xl transition-all duration-300 hover:scale-[1.01]">
                {/* Enhanced Block Header */}
                <div className="bg-gradient-to-r from-slate-50/80 to-gray-50/80 px-6 py-4 border-b border-gray-200/50">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-4">
                      <div className="relative">
                        <div className="w-12 h-12 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-2xl flex items-center justify-center text-white font-bold text-lg shadow-lg">
                          {i + 1}
                        </div>
                        {(block.audio_url && block.video_url) && (
                          <div className="absolute -top-2 -right-2 w-5 h-5 bg-green-500 rounded-full border-2 border-white flex items-center justify-center">
                            <CheckCircle size={12} className="text-white" />
                          </div>
                        )}
                      </div>
                      <div>
                        <h3 className="font-bold text-gray-900 text-lg">Block {i + 1}</h3>
                        <div className="flex items-center gap-4 text-sm text-gray-500">
                          <span className="flex items-center gap-1">
                            <Clock size={14} />
                            {block.target_sec}s
                          </span>
                          <span className="flex items-center gap-1">
                            {block.audio_url ? (
                              <><CheckCircle size={14} className="text-green-500" /> Audio Ready</>
                            ) : (
                              <><AlertCircle size={14} className="text-amber-500" /> No Audio</>
                            )}
                          </span>
                          <span className="flex items-center gap-1">
                            {block.video_url ? (
                              <><CheckCircle size={14} className="text-green-500" /> Video Ready</>
                            ) : (
                              <><AlertCircle size={14} className="text-amber-500" /> No Video</>
                            )}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-3">
                      <button
                        onClick={() => handleGenerateAudio(i)}
                        disabled={generatingAudio.has(i)}
                        className="flex items-center gap-2 bg-gradient-to-r from-blue-500 to-blue-600 text-white px-4 py-2.5 rounded-xl hover:from-blue-600 hover:to-blue-700 transition-all duration-200 font-medium shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105"
                      >
                        {generatingAudio.has(i) ? (
                          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        ) : (
                          <Volume2 size={16} />
                        )}
                        <span className="hidden sm:inline">Audio</span>
                      </button>
                      <button
                        onClick={() => handleGenerateVideo(i)}
                        disabled={generatingBlocks.has(i)}
                        className="flex items-center gap-2 bg-gradient-to-r from-green-500 to-green-600 text-white px-4 py-2.5 rounded-xl hover:from-green-600 hover:to-green-700 transition-all duration-200 font-medium shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105"
                      >
                        {generatingBlocks.has(i) ? (
                          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        ) : (
                          <Video size={16} />
                        )}
                        <span className="hidden sm:inline">Video</span>
                      </button>
                    </div>
                  </div>
                </div>

                {/* Enhanced Block Content */}
                <div className="p-6 space-y-6">
                  {/* Script Content */}
                  <div className="space-y-3">
                    <label className="block text-sm font-bold text-gray-700 flex items-center gap-2">
                      <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                      Script Content
                    </label>
                    <textarea
                      className="w-full border-2 border-gray-200 rounded-2xl p-4 bg-white/50 backdrop-blur-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none transition-all duration-200 hover:border-gray-300 text-gray-900"
                      rows={3}
                      value={block.text}
                      onChange={(e) => handleTextChange(i, e.target.value)}
                      placeholder="Enter your script content here..."
                    />
                  </div>

                  {/* Visual Prompt */}
                  <div className="space-y-3">
                    <label className="block text-sm font-bold text-gray-700 flex items-center gap-2">
                      <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                      Visual Style Prompt
                      <span className="text-xs text-gray-500 font-normal">(Optional)</span>
                    </label>
                    <textarea
                      className="w-full border-2 border-gray-200 rounded-2xl p-4 bg-white/50 backdrop-blur-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none transition-all duration-200 hover:border-gray-300 text-gray-900"
                      rows={2}
                      placeholder="Describe the visual style, setting, or mood for this scene..."
                      value={block.user_prompt || ''}
                      onChange={(e) => handlePromptChange(i, e.target.value)}
                    />
                  </div>

                  {/* Controls and Media Row */}
                  <div className="flex flex-wrap items-center gap-4 pt-2">
                    {/* Voice Selection */}
                    <div className="flex items-center gap-3">
                      <select
                        className="border-2 border-gray-200 rounded-xl px-4 py-2.5 bg-white/80 backdrop-blur-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all duration-200 hover:border-gray-300 font-medium"
                        value={block.voice_id}
                        onChange={(e) => handleVoiceChange(i, e.target.value)}
                      >
                        <option value="">Choose Voice</option>
                        {voices.map((v) => (
                          <option key={v.voice_id} value={v.voice_id}>
                            {v.name}
                          </option>
                        ))}
                      </select>

                      <button
                        onClick={() => playPreview(block.voice_id || "")}
                        className="flex items-center gap-2 text-gray-600 hover:text-indigo-600 px-3 py-2.5 rounded-xl hover:bg-indigo-50 transition-all duration-200 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                        disabled={!block.voice_id}
                      >
                        <Play size={16} />
                        <span className="hidden sm:inline">Preview</span>
                      </button>
                    </div>

                    {/* Audio Player */}
                    {block.audio_url && (
                      <div className="flex-1 min-w-0">
                        <audio
                          controls
                          src={`http://localhost:8000${block.audio_url}?t=${Date.now()}`}
                          className="w-full h-12 rounded-xl shadow-sm bg-gradient-to-r from-blue-50 to-indigo-50"
                        />
                      </div>
                    )}

                    {/* Video Preview Button */}
                    {block.video_url && (
                      <button
                        onClick={() => handlePlayVideo(block.video_url!)}
                        className="flex items-center gap-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white px-4 py-2.5 rounded-xl hover:from-purple-600 hover:to-pink-600 transition-all duration-200 font-medium shadow-lg transform hover:scale-105"
                      >
                        <Play size={16} />
                        <span className="hidden sm:inline">Watch</span>
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Enhanced iPhone Video Player */}
      {isPhoneVisible && selectedVideo && (
        <div 
          className="fixed z-50 select-none animate-in slide-in-from-bottom-4 duration-500"
          style={{ 
            left: phonePosition.x || window.innerWidth - 280, 
            top: phonePosition.y || window.innerHeight - 580,
            transform: isDragging ? 'scale(1.05) rotate(1deg)' : 'scale(1) rotate(0deg)',
            transition: isDragging ? 'none' : 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
          }}
        >
          {/* Enhanced Close Button */}
          <button
            onClick={() => {
              setIsPhoneVisible(false);
              setSelectedVideo(null);
            }}
            className="absolute -top-4 -right-4 w-10 h-10 bg-gradient-to-r from-red-500 to-pink-500 hover:from-red-600 hover:to-pink-600 rounded-full flex items-center justify-center transition-all duration-200 text-white hover:scale-110 shadow-2xl z-10 border-2 border-white"
          >
            <X size={18} />
          </button>

          {/* iPhone Mockup with Enhanced Design */}
          <div className="relative filter drop-shadow-2xl">
            {/* iPhone Frame */}
            <div className="relative w-64 h-[550px] bg-gradient-to-b from-gray-800 to-black rounded-[2.8rem] p-2 shadow-2xl">
              
              {/* Drag Handle */}
              <div 
                className="absolute top-0 left-0 right-0 h-20 rounded-t-[2.8rem] cursor-grab active:cursor-grabbing z-30 flex flex-col items-center justify-center group"
                onMouseDown={handleMouseDown}
              >
                <div className="w-10 h-1.5 bg-white/20 rounded-full mt-6 group-hover:bg-white/40 transition-colors duration-200"></div>
                <div className="w-6 h-1 bg-white/10 rounded-full mt-1 group-hover:bg-white/20 transition-colors duration-200"></div>
              </div>

              {/* iPhone Screen */}
              <div className="w-full h-full bg-black rounded-[2.3rem] overflow-hidden relative border border-gray-700">
                {/* Dynamic Island */}
                <div className="absolute top-2.5 left-1/2 transform -translate-x-1/2 w-28 h-6 bg-black rounded-full z-20 border border-gray-800"></div>
                
                {/* Screen Content */}
                <div className="w-full h-full bg-black rounded-[2.3rem] flex flex-col">
                  {/* Enhanced Status Bar */}
                  <div className="h-12 flex items-center justify-between px-6 text-white text-sm font-medium bg-gradient-to-b from-gray-900 to-black">
                    <div className="flex items-center gap-2">
                      <span>9:41</span>
                      <div className="flex gap-1">
                        <div className="w-1 h-1 bg-white rounded-full animate-pulse"></div>
                        <div className="w-1 h-1 bg-white rounded-full animate-pulse" style={{animationDelay: '0.2s'}}></div>
                        <div className="w-1 h-1 bg-white rounded-full animate-pulse" style={{animationDelay: '0.4s'}}></div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="text-xs">100%</div>
                      <div className="w-6 h-3 border border-white/60 rounded-sm">
                        <div className="w-full h-full bg-green-500 rounded-sm"></div>
                      </div>
                    </div>
                  </div>

                  {/* Video Container */}
                  <div className="flex-1 flex flex-col bg-black relative overflow-hidden">
                    <video
                      controls
                      autoPlay
                      src={selectedVideo}
                      className="w-full h-full object-cover rounded-b-[2.3rem]"
                    />
                    
                    {/* Video Overlay Effects */}
                    <div className="absolute inset-0 bg-gradient-to-t from-black/20 via-transparent to-black/10 pointer-events-none rounded-b-[2.3rem]"></div>
                  </div>
                </div>
              </div>

              {/* iPhone Physical Details */}
              <div className="absolute -left-1 top-20 w-1 h-8 bg-gray-600 rounded-l-md"></div>
              <div className="absolute -left-1 top-32 w-1 h-12 bg-gray-600 rounded-l-md"></div>
              <div className="absolute -left-1 top-48 w-1 h-12 bg-gray-600 rounded-l-md"></div>
              <div className="absolute -right-1 top-36 w-1 h-16 bg-gray-600 rounded-r-md"></div>
            </div>

            {/* iPhone Reflection and Glow */}
            <div className="absolute inset-0 bg-gradient-to-br from-white/10 via-transparent to-transparent rounded-[2.8rem] pointer-events-none"></div>
            <div className="absolute -inset-2 bg-gradient-to-r from-blue-500/20 via-purple-500/20 to-pink-500/20 rounded-[3rem] blur-xl -z-10 opacity-60"></div>
          </div>
        </div>
      )}
    </div>
  );
}