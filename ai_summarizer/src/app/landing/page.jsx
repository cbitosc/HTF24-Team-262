"use client";
import React, { useState } from 'react';
import { Upload, Youtube, FileVideo, CheckCircle, Loader2, Sun, Moon } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useTheme } from 'next-themes';
import BackgroundLinesDemo from '../background/page';
import Chatbot from '../bot/page';

const API_URL = 'http://127.0.0.1:5000/summarize';
const CLIP_API_URL = 'http://127.0.0.1:5000/summarize_video';

const LandingPage = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [summary, setSummary] = useState('');
  const [videoSummaryUrl, setVideoSummaryUrl] = useState('');
  const [clipUrl, setClipUrl] = useState('');
  const [language, setLanguage] = useState('en');
  const [summaryLength, setSummaryLength] = useState(60);
  const { theme, setTheme } = useTheme();

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setIsProcessing(true);
    setUploadSuccess(false);
    setSummary('');
    setVideoSummaryUrl('');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('language', language);

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        setSummary(data.summary);
        setVideoSummaryUrl(data.videoSummaryUrl);
        setUploadSuccess(true);
      } else {
        alert('Failed to summarize the video. Please try again.');
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('An error occurred. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleYoutubeUrlSubmit = async (e) => {
    e.preventDefault();
    if (!youtubeUrl) return;

    setIsProcessing(true);
    setUploadSuccess(false);
    setSummary('');
    setVideoSummaryUrl('');

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: youtubeUrl, language:language }),
      });

      if (response.ok) {
        const data = await response.json();
        setSummary(data.summary);
        setVideoSummaryUrl(data.videoSummaryUrl);
        setUploadSuccess(true);
      } else {
        alert('Failed to summarize the video. Please try again.');
      }
    } catch (error) {
      console.error('Error with YouTube URL:', error);
      alert('An error occurred. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleClipGeneration = async (e) => {
    e.preventDefault();
    if (!youtubeUrl) return;

    setIsProcessing(true);
    setClipUrl('');

    try {
      const response = await fetch(CLIP_API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: youtubeUrl,
          length: summaryLength,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        console.log(data)
        setClipUrl(data.path);
      } else {
        alert('Failed to generate the clip. Please try again.');
      }
    } catch (error) {
      console.error('Error generating clip:', error);
      alert('An error occurred. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen dark:bg-black bg-white transition-colors duration-300">
       <BackgroundLinesDemo/>
        <Chatbot />
      <div className="fixed top-4 right-4 z-50">
        <Button
          variant="outline"
          size="icon"
          className="rounded-full"
          onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
        >
          <Sun className="h-5 w-5 rotate-0 scale-100 transition-transform dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-transform dark:rotate-0 dark:scale-100" />
        </Button>
      </div>
       
{/* 
      <div className="container mx-auto px-4 pt-20 pb-16 text-center max-w-5xl">
        <div className="space-y-6 mx-auto">
          <div className="inline-block">
            <h1 className="text-4xl md:text-6xl font-bold tracking-tight">
              Transform Videos into
              <div className="relative inline-block ml-2">
                <span className="bg-gradient-to-r from-blue-600 to-violet-600 bg-clip-text text-transparent">
                  Quick Summaries
                </span>
              </div>
            </h1>
          
          </div>
          <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto">
            Using advanced AI to create concise summaries of any video content.
            Upload MP4 files or paste YouTube URLs - get insights in seconds.
          </p>
        </div>
      </div> */}

      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <Card className="mx-auto backdrop-blur-sm bg-card/95">
          <CardContent className="pt-6">
            <Tabs defaultValue="upload" className="w-full">
              <TabsList className="grid w-full grid-cols-3 mb-8">
                <TabsTrigger value="upload" className="flex items-center gap-2 text-sm">
                  <FileVideo className="h-4 w-4" />
                  Upload Video
                </TabsTrigger>
                <TabsTrigger value="youtube" className="flex items-center gap-2 text-sm">
                  <Youtube className="h-4 w-4" />
                  YouTube URL
                </TabsTrigger>
                <TabsTrigger value="clip" className="flex items-center gap-2 text-sm">
                  <Youtube className="h-4 w-4" />
                  YouTube Clipper
                </TabsTrigger>
              </TabsList>

              <div className="mb-4">
                <Select value={language} onValueChange={setLanguage}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select Language" />
                  </SelectTrigger>
                  <SelectContent>
               
  <SelectItem value="english">English</SelectItem>
  <SelectItem value="hindi">Hindi</SelectItem>
  <SelectItem value="bengali">Bengali</SelectItem>
  <SelectItem value="telugu">Telugu</SelectItem>
  <SelectItem value="tamil">Tamil</SelectItem>
  <SelectItem value="marathi">Marathi</SelectItem>
  <SelectItem value="gujarati">Gujarati</SelectItem>
  <SelectItem value="kannada">Kannada</SelectItem>


                  </SelectContent>
                </Select>
              </div>

              <TabsContent value="upload">
                <div className="space-y-4">
                  <Input
                    type="file"
                    accept="video/mp4"
                    onChange={handleFileUpload}
                    className="w-full text-base py-6"
                  />
                  {uploadSuccess && (
                    <Alert>
                      <CheckCircle className="h-4 w-4" />
                      <AlertDescription>Video uploaded successfully!</AlertDescription>
                    </Alert>
                  )}
                </div>
              </TabsContent>

              <TabsContent value="youtube">
                <form onSubmit={handleYoutubeUrlSubmit} className="space-y-4">
                  <Input
                    type="url"
                    placeholder="Paste YouTube URL..."
                    className="w-full text-base py-6"
                    value={youtubeUrl}
                    onChange={(e) => setYoutubeUrl(e.target.value)}
                  />
                  <Button
                    type="submit"
                    className="w-full py-6 text-base transition-all hover:scale-105"
                    size="lg"
                    disabled={isProcessing}
                  >
                    {isProcessing ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Processing...
                      </>
                    ) : (
                      'Summarize'
                    )}
                  </Button>
                </form>
              </TabsContent>

              <TabsContent value="clip">
                <form onSubmit={handleClipGeneration} className="space-y-4">
                  <Input
                    type="url"
                    placeholder="Paste YouTube URL for Clipping..."
                    className="w-full text-base py-6"
                    value={youtubeUrl}
                    onChange={(e) => setYoutubeUrl(e.target.value)}
                  />
                  <Input
                    type="number"
                    placeholder="Enter summary length in seconds"
                    className="w-full text-base py-6"
                    value={summaryLength}
                    onChange={(e) => setSummaryLength(e.target.value)}
                  />
                  <Button
                    type="submit"
                    className="w-full py-6 text-base transition-all hover:scale-105"
                    size="lg"
                    disabled={isProcessing}
                  >
                    {isProcessing ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Generating Clip...
                      </>
                    ) : (
                      'Generate Clip'
                    )}
                  </Button>
                </form>
              </TabsContent>
            </Tabs>
                    {/* Render the summary if available */}
            {summary && (
              <Card className="mt-6 p-4">
                <h3 className="text-lg font-semibold mb-2">Summary</h3>
                <p className="dark:text-white text-black">{summary}</p>
              </Card>
            )}

            {/* Render the summarized video if available */}
            {videoSummaryUrl && (
              <Card className="mt-6 p-4">
                <h3 className="text-lg font-semibold mb-2">Summarized Video</h3>
                <video controls className="w-full">
                  <source src={videoSummaryUrl} type="video/mp4" />
                  Your browser does not support the video tag.
                </video>
              </Card>
            )}

            {/* Render the clip video if available */}
            {clipUrl && (
  <Card className="mt-6 p-4">
    <h3 className="text-lg font-semibold mb-2">Generated Clip</h3>
    <video key={clipUrl} controls className="w-full">
      <source src={clipUrl} type="video/mp4" />
      Your browser does not support the video tag.
    </video>
    
  </Card>
)}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default LandingPage;