"use client";
import Image from "next/image";
import LandingPage from "./landing/page";
import ThisCantBeReached from "./thisSiteCanBeReached/page";
import { useState, useEffect } from "react";

export default function Home() {
  // Initialize with false to match server-side state
  const [showThisCantBeReached, setShowThisCantBeReached] = useState(false);

  // Handle the transition effect on the client side only
  useEffect(() => {
    // Set to true immediately when component mounts
    setShowThisCantBeReached(true);

    // Set up the timer to hide after 5.4 seconds
    const timer = setTimeout(() => {
      setShowThisCantBeReached(false);
    }, 5400);

    // Clean up the timer if component unmounts
    return () => clearTimeout(timer);
  }, []); // Empty dependency array means this runs once on mount

  return (
    <>
      {showThisCantBeReached ? (
        <ThisCantBeReached />
      ) : (
        <LandingPage />
      )}
    </>
  );
}