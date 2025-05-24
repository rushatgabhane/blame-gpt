import React from 'react';

interface VideoBackgroundProps {
  src: string;
  opacity?: number;
}

const VideoBackground: React.FC<VideoBackgroundProps> = ({ src, opacity }) => {
  return (
    <div className="video-banner">
      <video
        autoPlay
        loop
        muted
        playsInline
        style={{
          width: '100%',
          height: 'auto',
          imageRendering: 'pixelated',
          userSelect: 'none',
          opacity: opacity,
          // filter: 'blur(2px) brightness(0.7)',
        }}
      >
        <source src={src} type="video/mp4" />
      </video>
    </div>
  );
};

export default VideoBackground;
