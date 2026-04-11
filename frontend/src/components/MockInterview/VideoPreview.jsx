import React, { useEffect, useRef, useState } from 'react';
import { Camera, CameraOff, Monitor } from 'lucide-react';

const VideoPreview = () => {
    const videoRef = useRef(null);
    const [stream, setStream] = useState(null);
    const [isActive, setIsActive] = useState(false);
    const [error, setError] = useState(null);

    const startCamera = async () => {
        try {
            const mediaStream = await navigator.mediaDevices.getUserMedia({ 
                video: { width: 1280, height: 720 }, 
                audio: false 
            });
            setStream(mediaStream);
            if (videoRef.current) {
                videoRef.current.srcObject = mediaStream;
            }
            setIsActive(true);
            setError(null);
        } catch (err) {
            console.error('Error accessing camera:', err);
            setError('Camera access denied or unavailable.');
            setIsActive(false);
        }
    };

    const stopCamera = () => {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            setStream(null);
        }
        setIsActive(false);
    };

    useEffect(() => {
        return () => stopCamera();
    }, []);

    return (
        <div className="mock-video-container">
            <div className={`mock-video-feed ${isActive ? 'active' : ''}`}>
                {isActive ? (
                    <video 
                        ref={videoRef} 
                        autoPlay 
                        playsInline 
                        muted 
                        className="mock-video-element"
                    />
                ) : (
                    <div className="mock-video-placeholder">
                        <CameraOff size={40} strokeWidth={1.5} />
                        <p>{error || 'Camera is off'}</p>
                    </div>
                )}
                
                <div className="mock-video-overlay">
                    <div className="mock-video-badge">
                        <span className="mock-video-dot"></span>
                        {isActive ? 'Live Preview' : 'Camera Off'}
                    </div>
                </div>
            </div>
            
            <div className="mock-video-controls">
                <button 
                    className={`mock-video-toggle ${isActive ? 'active' : ''}`}
                    onClick={isActive ? stopCamera : startCamera}
                    title={isActive ? 'Turn off camera' : 'Turn on camera'}
                >
                    {isActive ? <CameraOff size={18} /> : <Camera size={18} />}
                    {isActive ? 'Stop Video' : 'Start Video'}
                </button>
            </div>
        </div>
    );
};

export default VideoPreview;
