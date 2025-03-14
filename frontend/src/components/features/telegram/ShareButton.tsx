import { Button } from '@/components/ui/common/button';
import React from 'react';

interface ShareButtonProps {
    text: string;
  }

const ShareButton: React.FC<ShareButtonProps> = ({ text }) => {
  const shareUrl = 'https://example.com';
  const shareText = 'Посмотрите это!';

  const handleShare = () => {
    const telegramUrl = `https://t.me/share/url?url=${encodeURIComponent(shareUrl)}&text=${encodeURIComponent(shareText)}`;
    window.open(telegramUrl, '_blank');
  };

  return (
    <Button className='w-full rounded-xl text-center m-2 hover:bg-foreground'
      onClick={handleShare} 
    >
      {text}
    </Button>
  );
};

export default ShareButton;