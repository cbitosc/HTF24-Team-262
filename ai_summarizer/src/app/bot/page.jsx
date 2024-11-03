"use client";

import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
} from "../../components/ui/dialog";
import { Button } from "../../components/ui/button";
import {
  Avatar,
  AvatarImage,
  AvatarFallback,
} from "../../components/ui/avatar";
import { ScrollArea } from "../../components/ui/scroll-area";
import { Input } from "../../components/ui/input";
import { VisuallyHidden } from '@radix-ui/react-visually-hidden';

export default function Chatbot() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "Hello! I'm an AI assistant. How can I help you today?",
    },
  ]);
  const [input, setInput] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingDots, setLoadingDots] = useState(".");

  useEffect(() => {
    let interval;
    if (isLoading) {
      interval = setInterval(() => {
        setLoadingDots((prev) => (prev.length < 3 ? prev + "." : "."));
        setMessages((prevMessages) => [
          ...prevMessages.slice(0, -1),
          { role: "assistant", content: loadingDots },
        ]);
      }, 500);
    } else {
      setLoadingDots(".");
    }
    return () => clearInterval(interval);
  }, [isLoading, loadingDots]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (input.trim() === "") return;

    const userMessage = {
      role: "user",
      content: input,
    };

    setMessages((prevMessages) => [...prevMessages, userMessage]);
    setInput("");

    const payload = {
      messages: [...messages, userMessage],
      useRag: true,
      llm: "gpt-3.5-turbo",
      similarityMetric: "cosine",
    };

    setIsLoading(true);

    setMessages((prevMessages) => [
      ...prevMessages,
      { role: "assistant", content: loadingDots },
    ]);

    try {
      const chatResponse = await fetch("http://localhost:5000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const chatData = await chatResponse.json();
      const assistantMessage = {
        role: "assistant",
        content: chatData.answer,
      };

      setMessages((prevMessages) => [
        ...prevMessages.slice(0, -1),
        assistantMessage,
      ]);
    } catch (error) {
      console.error("Error fetching response:", error);
      const errorMessage = {
        role: "assistant",
        content: "There was an error getting a response from the server.",
      };
      setMessages((prevMessages) => [
        ...prevMessages.slice(0, -1),
        errorMessage,
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-gradient-to-br from-gray-800 to-black text-white dark:text-black dark:from-gray-100 dark:to-gray-200 z-50">
      <Button
        variant="outline"
        size="icon"
        className="rounded-full fixed bottom-4 right-4 bg-gradient-to-r from-gray-700 to-black text-white h-16 w-44 hover:bg-gradient-to-r hover:from-gray-600 hover:to-black shadow-lg dark:bg-gradient-to-r dark:from-gray-300 dark:to-gray-100 dark:text-black dark:hover:from-gray-200 dark:hover:to-gray-300 hover:text-white"
        onClick={() => setIsOpen(true)}
      >
        AI Assistant
        <img className="h-12 w-12 ml-2 rounded-full" src="./bot.png" alt="Bot Icon" />
        <span className="sr-only">Open chatbot</span>
      </Button>
      <Dialog open={isOpen} onOpenChange={setIsOpen} className="bg-gray-100 dark:bg-gray-900">
        <DialogContent className="lg:w-[465px] sm:w-[350px] rounded-lg shadow-2xl">
          <div className="flex flex-col h-[600px] bg-gradient-to-br from-gray-900 to-black dark:from-gray-100 dark:to-gray-200">
            <DialogHeader className="border-b px-4 py-3 bg-gradient-to-r from-gray-800 to-black dark:from-gray-300 dark:to-gray-200 hover:bg-gradient-to-r hover:from-gray-700 hover:to-gray-800 dark:hover:from-gray-200 dark:hover:to-gray-100">
              <DialogTitle>
                <VisuallyHidden>Chat with Video Summarizer - AI Assistant</VisuallyHidden>
              </DialogTitle>
              <div className="flex items-center gap-3">
                <Avatar>
                  <AvatarImage src="/bot.png" alt="Bot Avatar" />
                  <AvatarFallback>
                    <img src="./bot.png" alt="Bot" />
                  </AvatarFallback>
                </Avatar>
                <div>
                  <p className="font-medium text-gray-200 dark:text-gray-800">
                    Video Summarizer - AI Assistant
                  </p>
                  <p className="text-sm text-gray-400 dark:text-gray-600">Online</p>
                </div>
              </div>
            </DialogHeader>
            <ScrollArea className="flex-1 p-4 overflow-y-auto bg-gradient-to-b from-black to-gray-900 dark:from-gray-100 dark:to-gray-200">
              <div className="space-y-4">
                {messages.map((message, index) => (
                  <div
                    key={index}
                    className={`flex w-max lg:max-w-96 sm:max-w-64 flex-col gap-2 rounded-lg px-4 py-2 text-sm break-words shadow-md ${
                      message.role === "user"
                        ? "ml-auto bg-gray-700 text-gray-100 hover:bg-gray-600 dark:bg-gray-200 dark:text-gray-900 dark:hover:bg-gray-300"
                        : "bg-gray-800 text-gray-300 hover:bg-gray-700 dark:bg-gray-100 dark:text-gray-900 dark:hover:bg-gray-200"
                    }`}
                  >
                    <p style={{ whiteSpace: "pre-wrap" }}>
                      {typeof message.content === "string" ? message.content : ""}
                    </p>
                    {typeof message.content !== "string" && message.content}
                  </div>
                ))}
              </div>
            </ScrollArea>
            <DialogFooter className="border-t px-4 py-3 bg-gradient-to-r from-black to-gray-800 dark:from-gray-200 dark:to-gray-100 hover:bg-gradient-to-r hover:from-gray-700 hover:to-gray-800 dark:hover:from-gray-100 dark:hover:to-gray-200">
              <form
                onSubmit={handleSendMessage}
                className="flex items-center w-full space-x-2"
              >
                <Input
                  id="message"
                  placeholder="Type your message..."
                  className="flex-1 border border-gray-500 dark:text-black text-white rounded-lg p-2 focus:border-gray-400 focus:ring focus:ring-gray-300 dark:border-gray-300 dark:focus:border-gray-600 dark:focus:ring-gray-500"
                  autoComplete="off"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                />
                <Button type="submit" className="rounded-full bg-gray-700 hover:bg-gray-800 dark:bg-gray-200 dark:hover:bg-gray-300" size="icon">
                  <SendIcon className="text-white dark:text-gray-900 h-8 w-8" />
                  <span className="sr-only">Send</span>
                </Button>
              </form>
            </DialogFooter>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}


// SendIcon remains unchanged
function SendIcon(props) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="m22 2-7 20-4-9-9-4Z" />
      <path d="M22 2 11 13" />
    </svg>
  );
}
