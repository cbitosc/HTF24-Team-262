import React from "react";
import { BackgroundLines } from "@/components/ui/background-lines";

export default function BackgroundLinesDemo() {
  return (
    (<BackgroundLines className="flex items-center justify-center w-full flex-col  px-4">
      <h2
        className="bg-clip-text text-transparent text-center bg-gradient-to-b from-neutral-900 to-neutral-700 dark:from-neutral-600 dark:to-white text-2xl md:text-4xl lg:text-7xl font-sans py-2 md:pt-10 md:pb-2 relative z-20 font-bold tracking-tight">
         ClipCraft.ai



      </h2>
      <p         className="bg-clip-text text-transparent text-center bg-gradient-to-b from-neutral-900 to-neutral-700 dark:from-neutral-600 dark:to-white text-2xl md:text-4xl lg:text-5xl font-sans md:pb-10 relative z-20 font-bold tracking-tight">

    Crafting Video Intelligence
    </p>
      <p
        className="max-w-xl mx-auto text-sm md:text-lg text-neutral-700 dark:text-neutral-400 text-center">
        Using advanced AI to create concise summaries of any video content.
            Upload MP4 files or paste YouTube URLs - get insights in seconds.
      </p>
    </BackgroundLines>)
  );
}
