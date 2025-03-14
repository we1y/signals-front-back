'use client'

import Automod from "@/components/features/Automod";
import Balance from "@/components/features/Balance";
import Signals from "@/components/features/Signals";
import Work from "@/components/features/Work";
import { useEffect } from "react";

export default function Home() {
  useEffect(() => {
    if (window.Telegram && window.Telegram.WebApp) {
      window.Telegram.WebApp.expand();
    }
  }, [])

  return (
    <div className='space-y-2 p-2 bg-gradient'>
        <Balance />
        <Work />
        <Signals />
        <Automod />
    </div>
  );
}

